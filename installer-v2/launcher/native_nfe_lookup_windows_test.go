//go:build windows

package main

import (
	"net/http/httptest"
	"strings"
	"testing"
)

func testKeyWithDV(base43 string) string {
	if len(base43) != 43 {
		panic("base precisa ter 43 digitos")
	}
	sum, weight := 0, 2
	for i := 42; i >= 0; i-- {
		sum += int(base43[i]-'0') * weight
		weight++
		if weight > 9 {
			weight = 2
		}
	}
	digit := 11 - (sum % 11)
	if digit >= 10 {
		digit = 0
	}
	return base43 + string(rune('0'+digit))
}

func TestValidNativeNfeKey(t *testing.T) {
	key := testKeyWithDV("3526091234567800012355001000012345123456789")
	if len(key) != 44 || !validNativeNfeKey(key) {
		t.Fatalf("chave valida rejeitada: %s", key)
	}
	bad := key[:43] + "9"
	if bad == key {
		bad = key[:43] + "8"
	}
	if validNativeNfeKey(bad) {
		t.Fatalf("DV invalido aceito: %s", bad)
	}
}

func TestValidateNativeNfeXML(t *testing.T) {
	key := testKeyWithDV("3526091234567800012355001000012345123456789")
	xml := `<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe"><NFe><infNFe Id="NFe` + key + `"><ide><mod>55</mod></ide></infNFe></NFe><protNFe><infProt><chNFe>` + key + `</chNFe><cStat>100</cStat></infProt></protNFe></nfeProc>`
	if err := validateNativeNfeXML([]byte(xml), key); err != nil {
		t.Fatalf("XML correto rejeitado: %v", err)
	}
	other := testKeyWithDV("3526091234567800012355001000012345123456790")
	if err := validateNativeNfeXML([]byte(xml), other); err == nil {
		t.Fatal("XML de outra chave foi aceito")
	}
}

func TestNativeNfeCORSDeniesInternetOrigins(t *testing.T) {
	r := httptest.NewRequest("POST", "http://127.0.0.1:47878/nfe-lookup", strings.NewReader(`{}`))
	r.Header.Set("Origin", "https://exemplo.com")
	w := httptest.NewRecorder()
	if nativeNfeSetCORS(w, r) {
		t.Fatal("origem externa foi aceita")
	}
	if w.Code != 403 {
		t.Fatalf("status inesperado: %d", w.Code)
	}
}

func TestNativeNfeCORSAllowsLoopback(t *testing.T) {
	r := httptest.NewRequest("POST", "http://127.0.0.1:47878/nfe-lookup", strings.NewReader(`{}`))
	r.Header.Set("Origin", "http://127.0.0.1:54321")
	w := httptest.NewRecorder()
	if !nativeNfeSetCORS(w, r) {
		t.Fatal("origem loopback foi rejeitada")
	}
	if got := w.Header().Get("Access-Control-Allow-Origin"); got != "http://127.0.0.1:54321" {
		t.Fatalf("ACAO inesperado: %q", got)
	}
}
