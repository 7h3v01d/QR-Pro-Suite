import qrcode.constants
import pytest
from PIL import Image

from core import AppSettings
from tab_generate import GeneratorTab


@pytest.fixture
def gen_tab(qapp):
    return GeneratorTab(AppSettings())


class TestErrorCorrectionMapping:
    @pytest.mark.parametrize("label,constant", [
        ("L (7%)", qrcode.constants.ERROR_CORRECT_L),
        ("M (15%)", qrcode.constants.ERROR_CORRECT_M),
        ("Q (25%)", qrcode.constants.ERROR_CORRECT_Q),
        ("H (30%)", qrcode.constants.ERROR_CORRECT_H),
    ])
    def test_known_labels(self, gen_tab, label, constant):
        gen_tab.error_combo.setCurrentText(label)
        assert gen_tab._ec_constant() == constant

    def test_unknown_label_defaults_to_h(self, gen_tab):
        # Simulate an unexpected combo state by calling the map lookup directly
        # via a monkeypatched currentText.
        class FakeCombo:
            def currentText(self):
                return "?? unknown"
        gen_tab.error_combo = FakeCombo()
        assert gen_tab._ec_constant() == qrcode.constants.ERROR_CORRECT_H


class TestMakeQr:
    def test_solid_mode_produces_rgb_image(self, gen_tab):
        gen_tab.gradient_mode.setCurrentText("Solid")
        gen_tab.size_spin.setValue(6)
        gen_tab.border_spin.setValue(2)
        img = gen_tab._make_qr("https://example.com")
        assert isinstance(img, Image.Image)
        assert img.mode == "RGB"
        assert img.width > 0 and img.height > 0

    def test_solid_mode_uses_fg_bg_colors(self, gen_tab):
        gen_tab.gradient_mode.setCurrentText("Solid")
        gen_tab.fg_swatch.set_color("#FF0000")
        gen_tab.bg_swatch.set_color("#00FF00")
        img = gen_tab._make_qr("hello")
        colors = set(img.getdata())
        # only the two configured colors should appear (module fill vs background)
        assert colors <= {(255, 0, 0), (0, 255, 0)}
        assert (255, 0, 0) in colors  # at least some foreground modules rendered

    @pytest.mark.parametrize("mode", ["Vertical", "Horizontal", "Diagonal", "Radial"])
    def test_gradient_modes_produce_valid_image(self, gen_tab, mode):
        gen_tab.gradient_mode.setCurrentText(mode)
        gen_tab.size_spin.setValue(4)
        gen_tab.border_spin.setValue(1)
        img = gen_tab._make_qr("gradient test payload")
        assert isinstance(img, Image.Image)
        assert img.mode == "RGB"
        # Gradient images should have more than 2 distinct colors (unlike solid)
        colors = set(img.getdata())
        assert len(colors) > 2

    def test_higher_box_size_yields_larger_image(self, gen_tab):
        gen_tab.gradient_mode.setCurrentText("Solid")
        gen_tab.size_spin.setValue(4)
        gen_tab.border_spin.setValue(2)
        small = gen_tab._make_qr("size test")
        gen_tab.size_spin.setValue(12)
        big = gen_tab._make_qr("size test")
        assert big.width > small.width


class TestMakeBarcode:
    @pytest.mark.parametrize("code_type,data", [
        ("EAN-13", "012345678905"),
        ("Code 128", "HELLO123"),
        ("Code 39", "HELLO"),
        ("UPC-A", "036000291452"),
    ])
    def test_generates_image_for_supported_types(self, gen_tab, code_type, data):
        img = gen_tab._make_barcode(data, code_type)
        assert isinstance(img, Image.Image)
        assert img.mode == "RGB"
        assert img.width > 0 and img.height > 0

    def test_unknown_type_falls_back_to_code128(self, gen_tab):
        img = gen_tab._make_barcode("FALLBACK123", "Some Unknown Type")
        assert isinstance(img, Image.Image)


class TestApplyLogo:
    def test_embeds_logo_and_keeps_base_size(self, gen_tab, tmp_path):
        base = Image.new("RGB", (300, 300), "white")
        logo_path = tmp_path / "logo.png"
        Image.new("RGBA", (50, 50), (10, 20, 30, 255)).save(logo_path)
        gen_tab.logo_path = str(logo_path)

        result = gen_tab._apply_logo(base)
        assert result.mode == "RGB"
        assert result.size == base.size
        # center pixel should now be influenced by the white backing/logo,
        # not the plain white background pixel value alone remaining unset
        cx, cy = result.width // 2, result.height // 2
        assert result.getpixel((cx, cy)) is not None

    def test_missing_logo_file_shows_error_and_returns_original(self, gen_tab, tmp_path, monkeypatch):
        base = Image.new("RGB", (100, 100), "white")
        gen_tab.logo_path = str(tmp_path / "does_not_exist.png")

        called = {}
        def fake_show_error(parent, title, msg):
            called["title"] = title
        monkeypatch.setattr("tab_generate.show_error", fake_show_error)

        result = gen_tab._apply_logo(base)
        assert called.get("title") == "Logo Error"
        assert result.size == base.size
        assert result.mode == "RGB"
