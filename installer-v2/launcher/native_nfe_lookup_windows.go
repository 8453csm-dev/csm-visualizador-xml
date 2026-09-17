//go:build windows

package main

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"encoding/xml"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"syscall"
	"time"
	"unsafe"
)

const (
	nativeNfeProviderNfeio = "nfeio"
	nativeNfeMaxXMLBytes    = 25 * 1024 * 1024
)

var (
	crypt32                  = syscall.NewLazyDLL("crypt32.dll")
	procCryptProtectData     = crypt32.NewProc("CryptProtectData")
	procCryptUnprotectData   = crypt32.NewProc("CryptUnprotectData")
	procLocalFree            = kernel32.NewProc("LocalFree")
	nativeNfeRemoteMu        sync.Mutex
	nativeNfeRateMu          sync.Mutex
	nativeNfeRemoteRequests  []time.Time
	nativeNfeioBaseURL       = "https://nfe.api.nfe.io"
	nativeNfeHTTPClient      = &http.Client{Timeout: 55 * time.Second}
)

type dataBlob struct {
	cbData uint32
	pbData *byte
}

type nativeNfeLookupRequest struct {
	Key string `json:"key"`
}

type nativeNfeConfigRequest struct {
	Provider string `json:"provider"`
	APIKey   string `json:"api_key"`
	Clear    bool   `json:"clear"`
}

type nativeNfeConfigDisk struct {
	Provider       string `json:"provider"`
	APIKeyDPAPIB64 string `json:"api_key_dpapi_b64"`
}

type nativeNfeConfig struct {
	Provider string
	APIKey   string
}

type nativeNfeError struct {
	Code       string
	Message    string
	HTTPStatus int
}

func (e *nativeNfeError) Error() string { return e.Message }

func normalizeNativeNfeKey(value string) string {
	value = strings.ToUpper(strings.TrimSpace(value))
	var b strings.Builder
	b.Grow(44)
	for _, r := range value {
		if (r >= '0' && r <= '9') || (r >= 'A' && r <= 'Z') {
			b.WriteRune(r)
		}
	}
	return b.String()
}

func validNativeNfeKey(key string) bool {
	key = normalizeNativeNfeKey(key)
	if len(key) != 44 {
		return false
	}
	allDigits := true
	for i := 0; i < len(key); i++ {
		if key[i] < '0' || key[i] > '9' {
			allDigits = false
			break
		}
	}
	// Mantem compatibilidade futura com chaves que eventualmente passem a aceitar
	// caracteres alfanumericos. Para a chave numerica atual, valida tambem o DV.
	if !allDigits {
		return true
	}
	sum, weight := 0, 2
	for i := 42; i >= 0; i-- {
		sum += int(key[i]-'0') * weight
		weight++
		if weight > 9 {
			weight = 2
		}
	}
	digit := 11 - (sum % 11)
	if digit >= 10 {
		digit = 0
	}
	return digit == int(key[43]-'0')
}

func nativeNfeAppDataDir() string {
	base := strings.TrimSpace(os.Getenv("LOCALAPPDATA"))
	if base == "" {
		base = os.TempDir()
	}
	return filepath.Join(base, "CSM Visualizador XML")
}

func nativeNfeConfigPath() string {
	return filepath.Join(nativeNfeAppDataDir(), "config", "consulta-nfe.json")
}

func nativeNfeCachePath(key string) string {
	return filepath.Join(nativeNfeAppDataDir(), "consultas-nfe", key+".xml")
}

func blobFromBytes(data []byte) dataBlob {
	if len(data) == 0 {
		return dataBlob{}
	}
	return dataBlob{cbData: uint32(len(data)), pbData: &data[0]}
}

func copyBlob(data dataBlob) []byte {
	if data.cbData == 0 || data.pbData == nil {
		return nil
	}
	return append([]byte(nil), unsafe.Slice(data.pbData, int(data.cbData))...)
}

func dpapiProtect(plain []byte) ([]byte, error) {
	if len(plain) == 0 {
		return nil, errors.New("segredo vazio")
	}
	in := blobFromBytes(plain)
	var out dataBlob
	r, _, callErr := procCryptProtectData.Call(
		uintptr(unsafe.Pointer(&in)),
		0,
		0,
		0,
		0,
		0x01, // CRYPTPROTECT_UI_FORBIDDEN
		uintptr(unsafe.Pointer(&out)),
	)
	if r == 0 {
		return nil, fmt.Errorf("DPAPI ProtectData falhou: %v", callErr)
	}
	defer procLocalFree.Call(uintptr(unsafe.Pointer(out.pbData)))
	return copyBlob(out), nil
}

func dpapiUnprotect(cipher []byte) ([]byte, error) {
	if len(cipher) == 0 {
		return nil, errors.New("segredo protegido vazio")
	}
	in := blobFromBytes(cipher)
	var out dataBlob
	r, _, callErr := procCryptUnprotectData.Call(
		uintptr(unsafe.Pointer(&in)),
		0,
		0,
		0,
		0,
		0x01, // CRYPTPROTECT_UI_FORBIDDEN
		uintptr(unsafe.Pointer(&out)),
	)
	if r == 0 {
		return nil, fmt.Errorf("DPAPI UnprotectData falhou: %v", callErr)
	}
	defer procLocalFree.Call(uintptr(unsafe.Pointer(out.pbData)))
	return copyBlob(out), nil
}

func saveNativeNfeConfig(provider, apiKey string) error {
	provider = strings.ToLower(strings.TrimSpace(provider))
	if provider == "" {
		provider = nativeNfeProviderNfeio
	}
	if provider != nativeNfeProviderNfeio {
		return errors.New("provedor de consulta ainda não suportado")
	}
	apiKey = strings.TrimSpace(apiKey)
	if apiKey == "" {
		return errors.New("informe a chave da API")
	}
	protected, err := dpapiProtect([]byte(apiKey))
	if err != nil {
		return err
	}
	payload, err := json.MarshalIndent(nativeNfeConfigDisk{
		Provider:       provider,
		APIKeyDPAPIB64: base64.StdEncoding.EncodeToString(protected),
	}, "", "  ")
	if err != nil {
		return err
	}
	path := nativeNfeConfigPath()
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return err
	}
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, payload, 0o600); err != nil {
		return err
	}
	if err := os.Rename(tmp, path); err != nil {
		_ = os.Remove(tmp)
		return err
	}
	return nil
}

func loadNativeNfeConfig() (nativeNfeConfig, error) {
	if fromEnv := strings.TrimSpace(os.Getenv("CSM_NFEIO_API_KEY")); fromEnv != "" {
		return nativeNfeConfig{Provider: nativeNfeProviderNfeio, APIKey: fromEnv}, nil
	}
	data, err := os.ReadFile(nativeNfeConfigPath())
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return nativeNfeConfig{Provider: nativeNfeProviderNfeio}, nil
		}
		return nativeNfeConfig{}, err
	}
	var disk nativeNfeConfigDisk
	if err := json.Unmarshal(data, &disk); err != nil {
		return nativeNfeConfig{}, errors.New("configuração da consulta NF-e inválida")
	}
	if disk.Provider == "" {
		disk.Provider = nativeNfeProviderNfeio
	}
	cipher, err := base64.StdEncoding.DecodeString(disk.APIKeyDPAPIB64)
	if err != nil {
		return nativeNfeConfig{}, errors.New("chave protegida da consulta NF-e inválida")
	}
	plain, err := dpapiUnprotect(cipher)
	if err != nil {
		return nativeNfeConfig{}, errors.New("não foi possível desbloquear a chave da API neste usuário do Windows")
	}
	return nativeNfeConfig{Provider: strings.ToLower(disk.Provider), APIKey: strings.TrimSpace(string(plain))}, nil
}

func deleteNativeNfeConfig() error {
	err := os.Remove(nativeNfeConfigPath())
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	return err
}

func nativeNfeSetCORS(w http.ResponseWriter, r *http.Request) bool {
	origin := strings.TrimSpace(r.Header.Get("Origin"))
	if origin != "" {
		u, err := url.Parse(origin)
		if err != nil {
			http.Error(w, "origin inválida", http.StatusForbidden)
			return false
		}
		host := strings.ToLower(u.Hostname())
		if (u.Scheme != "http" && u.Scheme != "https") || (host != "127.0.0.1" && host != "localhost" && host != "::1") {
			http.Error(w, "origem não autorizada", http.StatusForbidden)
			return false
		}
		w.Header().Set("Access-Control-Allow-Origin", origin)
		w.Header().Add("Vary", "Origin")
	}
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
	return true
}

func writeNativeNfeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func nativeNfeErrorJSON(w http.ResponseWriter, err error) {
	var typed *nativeNfeError
	if errors.As(err, &typed) {
		writeNativeNfeJSON(w, typed.HTTPStatus, map[string]any{"ok": false, "code": typed.Code, "error": typed.Message})
		return
	}
	writeNativeNfeJSON(w, http.StatusInternalServerError, map[string]any{"ok": false, "code": "internal_error", "error": "Não foi possível concluir a consulta da NF-e."})
}

func (b *broker) handleNativeNfeConfig(w http.ResponseWriter, r *http.Request) {
	if !nativeNfeSetCORS(w, r) {
		return
	}
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}
	switch r.Method {
	case http.MethodGet:
		cfg, err := loadNativeNfeConfig()
		configured := err == nil && strings.TrimSpace(cfg.APIKey) != ""
		provider := nativeNfeProviderNfeio
		if cfg.Provider != "" {
			provider = cfg.Provider
		}
		writeNativeNfeJSON(w, http.StatusOK, map[string]any{
			"ok":         true,
			"provider":   provider,
			"configured": configured,
		})
	case http.MethodPost:
		var req nativeNfeConfigRequest
		if err := json.NewDecoder(io.LimitReader(r.Body, 32*1024)).Decode(&req); err != nil {
			writeNativeNfeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "Configuração inválida."})
			return
		}
		if req.Clear {
			if err := deleteNativeNfeConfig(); err != nil {
				nativeNfeErrorJSON(w, err)
				return
			}
			writeNativeNfeJSON(w, http.StatusOK, map[string]any{"ok": true, "provider": nativeNfeProviderNfeio, "configured": false})
			return
		}
		if err := saveNativeNfeConfig(req.Provider, req.APIKey); err != nil {
			writeNativeNfeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": err.Error()})
			return
		}
		writeNativeNfeJSON(w, http.StatusOK, map[string]any{"ok": true, "provider": nativeNfeProviderNfeio, "configured": true})
	default:
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
	}
}

func (b *broker) handleNativeNfeLookup(w http.ResponseWriter, r *http.Request) {
	if !nativeNfeSetCORS(w, r) {
		return
	}
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if ct := strings.ToLower(r.Header.Get("Content-Type")); ct != "" && !strings.HasPrefix(ct, "application/json") {
		writeNativeNfeJSON(w, http.StatusUnsupportedMediaType, map[string]any{"ok": false, "error": "Envie a consulta em JSON."})
		return
	}
	var req nativeNfeLookupRequest
	if err := json.NewDecoder(io.LimitReader(r.Body, 8*1024)).Decode(&req); err != nil {
		writeNativeNfeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "error": "Consulta inválida."})
		return
	}
	key := normalizeNativeNfeKey(req.Key)
	if !validNativeNfeKey(key) {
		writeNativeNfeJSON(w, http.StatusBadRequest, map[string]any{"ok": false, "code": "invalid_key", "error": "A chave de acesso da NF-e deve possuir 44 caracteres válidos."})
		return
	}

	path := nativeNfeCachePath(key)
	if data, err := os.ReadFile(path); err == nil && validateNativeNfeXML(data, key) == nil {
		b.queuePath(path)
		writeNativeNfeJSON(w, http.StatusOK, map[string]any{"ok": true, "key": key, "source": "cache", "opened": true})
		return
	}

	cfg, err := loadNativeNfeConfig()
	if err != nil || strings.TrimSpace(cfg.APIKey) == "" {
		writeNativeNfeJSON(w, http.StatusPreconditionRequired, map[string]any{
			"ok": false, "code": "config_required", "error": "Configure a chave da API uma única vez para consultar NF-e pela chave.",
		})
		return
	}

	// Serializa consultas externas para impedir duplo clique de gerar cobrança duplicada.
	nativeNfeRemoteMu.Lock()
	defer nativeNfeRemoteMu.Unlock()

	// Outro clique pode ter preenchido o cache enquanto esta requisição aguardava o lock.
	if data, err := os.ReadFile(path); err == nil && validateNativeNfeXML(data, key) == nil {
		b.queuePath(path)
		writeNativeNfeJSON(w, http.StatusOK, map[string]any{"ok": true, "key": key, "source": "cache", "opened": true})
		return
	}
	if !allowNativeNfeRemoteRequest() {
		writeNativeNfeJSON(w, http.StatusTooManyRequests, map[string]any{"ok": false, "code": "local_rate_limit", "error": "Muitas consultas em sequência. Aguarde um instante e tente novamente."})
		return
	}

	xmlData, err := fetchNativeNfeXML(cfg, key)
	if err != nil {
		nativeNfeErrorJSON(w, err)
		return
	}
	if err := validateNativeNfeXML(xmlData, key); err != nil {
		nativeNfeErrorJSON(w, &nativeNfeError{Code: "invalid_xml", Message: "O provedor respondeu, mas o XML não corresponde à chave consultada.", HTTPStatus: http.StatusBadGateway})
		return
	}
	if err := saveNativeNfeXML(path, xmlData); err != nil {
		nativeNfeErrorJSON(w, err)
		return
	}
	b.queuePath(path)
	writeNativeNfeJSON(w, http.StatusOK, map[string]any{"ok": true, "key": key, "source": cfg.Provider, "opened": true})
}

func allowNativeNfeRemoteRequest() bool {
	now := time.Now()
	cutoff := now.Add(-1 * time.Minute)
	nativeNfeRateMu.Lock()
	defer nativeNfeRateMu.Unlock()
	kept := nativeNfeRemoteRequests[:0]
	for _, t := range nativeNfeRemoteRequests {
		if t.After(cutoff) {
			kept = append(kept, t)
		}
	}
	nativeNfeRemoteRequests = kept
	if len(nativeNfeRemoteRequests) >= 20 {
		return false
	}
	nativeNfeRemoteRequests = append(nativeNfeRemoteRequests, now)
	return true
}

func fetchNativeNfeXML(cfg nativeNfeConfig, key string) ([]byte, error) {
	switch cfg.Provider {
	case nativeNfeProviderNfeio, "":
		return fetchNativeNfeFromNfeio(cfg.APIKey, key)
	default:
		return nil, &nativeNfeError{Code: "provider_unsupported", Message: "O provedor configurado ainda não é suportado por esta versão.", HTTPStatus: http.StatusBadRequest}
	}
}

func fetchNativeNfeFromNfeio(apiKey, key string) ([]byte, error) {
	endpoint := strings.TrimRight(nativeNfeioBaseURL, "/") + "/v2/productinvoices/" + url.PathEscape(key) + ".xml"
	req, err := http.NewRequest(http.MethodGet, endpoint, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", strings.TrimSpace(apiKey))
	req.Header.Set("Accept", "application/xml, text/xml;q=0.9, */*;q=0.1")
	req.Header.Set("User-Agent", "CSM-Visualizador-XML/native-nfe-lookup")
	resp, err := nativeNfeHTTPClient.Do(req)
	if err != nil {
		return nil, &nativeNfeError{Code: "provider_unavailable", Message: "O serviço de consulta não respondeu. Verifique a internet e tente novamente.", HTTPStatus: http.StatusBadGateway}
	}
	defer resp.Body.Close()
	limited := io.LimitReader(resp.Body, nativeNfeMaxXMLBytes+1)
	body, err := io.ReadAll(limited)
	if err != nil {
		return nil, &nativeNfeError{Code: "provider_read_error", Message: "Não foi possível ler a resposta do serviço de consulta.", HTTPStatus: http.StatusBadGateway}
	}
	if len(body) > nativeNfeMaxXMLBytes {
		return nil, &nativeNfeError{Code: "provider_response_too_large", Message: "A resposta da consulta excedeu o limite de segurança do Visualizador.", HTTPStatus: http.StatusBadGateway}
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, providerNativeNfeHTTPError(resp.StatusCode)
	}
	return body, nil
}

func providerNativeNfeHTTPError(status int) error {
	switch status {
	case http.StatusUnauthorized, http.StatusForbidden:
		return &nativeNfeError{Code: "provider_auth", Message: "A chave da API foi recusada. Abra Configurar consulta e confira a credencial.", HTTPStatus: http.StatusBadGateway}
	case http.StatusNotFound:
		return &nativeNfeError{Code: "not_found", Message: "A NF-e não foi localizada para essa chave de acesso.", HTTPStatus: http.StatusNotFound}
	case http.StatusPaymentRequired:
		return &nativeNfeError{Code: "provider_balance", Message: "O provedor informou saldo ou crédito insuficiente para realizar a consulta.", HTTPStatus: http.StatusPaymentRequired}
	case http.StatusTooManyRequests:
		return &nativeNfeError{Code: "provider_rate_limit", Message: "O provedor limitou temporariamente as consultas. Tente novamente em instantes.", HTTPStatus: http.StatusTooManyRequests}
	default:
		return &nativeNfeError{Code: "provider_error", Message: fmt.Sprintf("O serviço de consulta retornou erro HTTP %d.", status), HTTPStatus: http.StatusBadGateway}
	}
}

func validateNativeNfeXML(data []byte, key string) error {
	if len(data) == 0 {
		return errors.New("XML vazio")
	}
	dec := xml.NewDecoder(bytes.NewReader(data))
	matched := false
	for {
		tok, err := dec.Token()
		if errors.Is(err, io.EOF) {
			break
		}
		if err != nil {
			return fmt.Errorf("XML inválido: %w", err)
		}
		start, ok := tok.(xml.StartElement)
		if !ok {
			continue
		}
		local := strings.ToLower(start.Name.Local)
		if local == "infnfe" {
			for _, attr := range start.Attr {
				if strings.EqualFold(attr.Name.Local, "Id") {
					id := normalizeNativeNfeKey(strings.TrimPrefix(strings.TrimSpace(attr.Value), "NFe"))
					if id == key {
						matched = true
					}
				}
			}
		}
		if local == "chnfe" {
			var value string
			if err := dec.DecodeElement(&value, &start); err != nil {
				return fmt.Errorf("XML inválido: %w", err)
			}
			if normalizeNativeNfeKey(value) == key {
				matched = true
			}
		}
	}
	if !matched {
		return errors.New("XML não corresponde à chave consultada")
	}
	return nil
}

func saveNativeNfeXML(path string, data []byte) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return err
	}
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, data, 0o600); err != nil {
		return err
	}
	if err := os.Rename(tmp, path); err != nil {
		_ = os.Remove(tmp)
		return err
	}
	return nil
}
