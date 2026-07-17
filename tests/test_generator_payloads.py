import pytest

from core import AppSettings
from tab_generate import GeneratorTab


@pytest.fixture
def gen_tab(qapp):
    tab = GeneratorTab(AppSettings())
    return tab


def set_type(tab, type_name):
    tab.type_combo.setCurrentText(type_name)


class TestTextUrlPayload:
    def test_basic_text(self, gen_tab):
        set_type(gen_tab, "QR — Text / URL")
        gen_tab.f_text._fields["data"].setPlainText("https://anthropic.com")
        payload, label = gen_tab._get_payload()
        assert payload == "https://anthropic.com"
        assert label == payload

    def test_strips_whitespace(self, gen_tab):
        set_type(gen_tab, "QR — Text / URL")
        gen_tab.f_text._fields["data"].setPlainText("   hello world   ")
        payload, _ = gen_tab._get_payload()
        assert payload == "hello world"

    def test_empty_raises(self, gen_tab):
        set_type(gen_tab, "QR — Text / URL")
        gen_tab.f_text._fields["data"].setPlainText("   ")
        with pytest.raises(ValueError, match="Data cannot be empty"):
            gen_tab._get_payload()


class TestWifiPayload:
    def test_wpa(self, gen_tab):
        set_type(gen_tab, "QR — Wi-Fi")
        F = gen_tab.f_wifi._fields
        F["ssid"].setText("MyNetwork")
        F["pass"].setText("hunter2")
        F["enc"].setCurrentText("WPA/WPA2")
        F["hidden"].setChecked(False)
        payload, label = gen_tab._get_payload()
        assert payload == "WIFI:T:WPA;S:MyNetwork;P:hunter2;;"
        assert label == "Wi-Fi: MyNetwork"

    def test_open_network_maps_to_nopass(self, gen_tab):
        set_type(gen_tab, "QR — Wi-Fi")
        F = gen_tab.f_wifi._fields
        F["ssid"].setText("OpenNet")
        F["pass"].setText("")
        F["enc"].setCurrentText("None")
        payload, _ = gen_tab._get_payload()
        assert payload == "WIFI:T:nopass;S:OpenNet;P:;;"

    def test_hidden_flag_appended(self, gen_tab):
        set_type(gen_tab, "QR — Wi-Fi")
        F = gen_tab.f_wifi._fields
        F["ssid"].setText("Secret")
        F["pass"].setText("pw")
        F["enc"].setCurrentText("WEP")
        F["hidden"].setChecked(True)
        payload, _ = gen_tab._get_payload()
        assert payload == "WIFI:T:WEP;S:Secret;P:pw;H:true;;"

    def test_empty_ssid_raises(self, gen_tab):
        set_type(gen_tab, "QR — Wi-Fi")
        gen_tab.f_wifi._fields["ssid"].setText("  ")
        with pytest.raises(ValueError, match="SSID cannot be empty"):
            gen_tab._get_payload()


class TestVCardPayload:
    def test_minimal_vcard(self, gen_tab):
        set_type(gen_tab, "QR — vCard")
        F = gen_tab.f_vcard._fields
        F["name"].setText("Ada Lovelace")
        for key in ("title", "org", "phone", "email", "url", "addr"):
            F[key].setText("")
        payload, label = gen_tab._get_payload()
        assert payload.startswith("BEGIN:VCARD\nVERSION:3.0\nFN:Ada Lovelace\nN:Ada Lovelace")
        assert payload.endswith("END:VCARD")
        assert label == "vCard: Ada Lovelace"
        # optional fields omitted when blank
        assert "TITLE:" not in payload

    def test_full_vcard_includes_all_fields(self, gen_tab):
        set_type(gen_tab, "QR — vCard")
        F = gen_tab.f_vcard._fields
        F["name"].setText("Grace Hopper")
        F["title"].setText("Rear Admiral")
        F["org"].setText("US Navy")
        F["phone"].setText("+1 555 0100")
        F["email"].setText("grace@navy.mil")
        F["url"].setText("https://navy.mil")
        F["addr"].setText("Washington DC")
        payload, _ = gen_tab._get_payload()
        assert "TITLE:Rear Admiral" in payload
        assert "ORG:US Navy" in payload
        assert "TEL:+1 555 0100" in payload
        assert "EMAIL:grace@navy.mil" in payload
        assert "URL:https://navy.mil" in payload
        assert "ADR:Washington DC" in payload

    def test_empty_name_raises(self, gen_tab):
        set_type(gen_tab, "QR — vCard")
        gen_tab.f_vcard._fields["name"].setText("")
        with pytest.raises(ValueError, match="Name cannot be empty"):
            gen_tab._get_payload()


class TestEmailPayload:
    def test_email_payload(self, gen_tab):
        set_type(gen_tab, "QR — E-mail")
        F = gen_tab.f_email._fields
        F["to"].setText("a@b.com")
        F["subject"].setText("Hi")
        F["body"].setPlainText("Body text")
        payload, label = gen_tab._get_payload()
        assert payload == "MATMSG:TO:a@b.com;SUB:Hi;BODY:Body text;;"
        assert label == "Email to: a@b.com"

    def test_empty_recipient_raises(self, gen_tab):
        set_type(gen_tab, "QR — E-mail")
        gen_tab.f_email._fields["to"].setText("")
        with pytest.raises(ValueError, match="Recipient address cannot be empty"):
            gen_tab._get_payload()


class TestSmsPayload:
    def test_sms_payload(self, gen_tab):
        set_type(gen_tab, "QR — SMS")
        F = gen_tab.f_sms._fields
        F["num"].setText("+61400000000")
        F["msg"].setPlainText("hey")
        payload, label = gen_tab._get_payload()
        assert payload == "SMSTO:+61400000000:hey"
        assert label == "SMS: +61400000000"

    def test_empty_number_raises(self, gen_tab):
        set_type(gen_tab, "QR — SMS")
        gen_tab.f_sms._fields["num"].setText("")
        with pytest.raises(ValueError, match="Phone number cannot be empty"):
            gen_tab._get_payload()


class TestPhonePayload:
    def test_phone_payload(self, gen_tab):
        set_type(gen_tab, "QR — Phone")
        gen_tab.f_phone._fields["num"].setText("+61400000000")
        payload, label = gen_tab._get_payload()
        assert payload == "tel:+61400000000"
        assert label == "Phone: +61400000000"

    def test_empty_number_raises(self, gen_tab):
        set_type(gen_tab, "QR — Phone")
        gen_tab.f_phone._fields["num"].setText("")
        with pytest.raises(ValueError, match="Phone number cannot be empty"):
            gen_tab._get_payload()


class TestGeoPayload:
    def test_geo_payload_with_altitude(self, gen_tab):
        set_type(gen_tab, "QR — Geo Location")
        F = gen_tab.f_geo._fields
        F["lat"].setText("-27.4705")
        F["lon"].setText("153.0260")
        F["alt"].setText("15")
        payload, label = gen_tab._get_payload()
        assert payload == "geo:-27.4705,153.0260,15"
        assert label == "Geo: -27.4705, 153.0260"

    def test_missing_lat_raises(self, gen_tab):
        set_type(gen_tab, "QR — Geo Location")
        F = gen_tab.f_geo._fields
        F["lat"].setText("")
        F["lon"].setText("153.0260")
        with pytest.raises(ValueError, match="Lat/Lon cannot be empty"):
            gen_tab._get_payload()


class TestBitcoinPayload:
    def test_address_only(self, gen_tab):
        set_type(gen_tab, "QR — Bitcoin")
        F = gen_tab.f_btc._fields
        F["addr"].setText("1BoatSLRHtKNngkdXEeobR76b53LETtpyT")
        F["amount"].setText("")
        F["label"].setText("")
        F["msg"].setText("")
        payload, label = gen_tab._get_payload()
        assert payload == "bitcoin:1BoatSLRHtKNngkdXEeobR76b53LETtpyT"
        assert label == "BTC: 1BoatSLRHtKN…"  # addr[:12] + ellipsis

    def test_with_query_params(self, gen_tab):
        set_type(gen_tab, "QR — Bitcoin")
        F = gen_tab.f_btc._fields
        F["addr"].setText("1BoatSLRHtKNngkdXEeobR76b53LETtpyT")
        F["amount"].setText("0.05")
        F["label"].setText("Coffee")
        F["msg"].setText("Thanks")
        payload, _ = gen_tab._get_payload()
        assert payload == (
            "bitcoin:1BoatSLRHtKNngkdXEeobR76b53LETtpyT"
            "?amount=0.05&label=Coffee&message=Thanks"
        )

    def test_empty_address_raises(self, gen_tab):
        set_type(gen_tab, "QR — Bitcoin")
        gen_tab.f_btc._fields["addr"].setText("")
        with pytest.raises(ValueError, match="Bitcoin address cannot be empty"):
            gen_tab._get_payload()


class TestBarcodePayload:
    @pytest.mark.parametrize("code_type", ["EAN-13", "Code 128", "Code 39", "UPC-A"])
    def test_barcode_payload_passthrough(self, gen_tab, code_type):
        set_type(gen_tab, code_type)
        gen_tab.f_barcode._fields["data"].setText("012345678905")
        payload, label = gen_tab._get_payload()
        assert payload == "012345678905"
        assert label == payload

    def test_empty_barcode_data_raises(self, gen_tab):
        set_type(gen_tab, "EAN-13")
        gen_tab.f_barcode._fields["data"].setText("")
        with pytest.raises(ValueError, match="Barcode data cannot be empty"):
            gen_tab._get_payload()
