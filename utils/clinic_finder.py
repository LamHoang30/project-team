import math
import re
import unicodedata
from pathlib import Path
import urllib.parse
import pandas as pd
import requests
import streamlit as st
from utils.ui import tr

ROOT = Path(__file__).resolve().parent.parent
PROVINCES_CSV_PATH = ROOT / "data" / "provinces_34.csv"
HEADERS = {"User-Agent": "GlucoGuide-HealthScreening/1.0 (contact: support@glucoguide.edu.vn)"}

# Danh bạ chính thức đối chiếu từ provinces_34.csv:
# (Hotline, Mô tả tổng đài, URL trang đặt lịch / cổng thông tin chính thức của chính Bệnh viện)
CURATED_HOSPITAL_BOOKING = {
    # --- TP. HỒ CHÍ MINH ---
    "bệnh viện đại học y dược tp.hcm": (
        "1900 7178",
        "Tổng đài đặt lịch khám: 1900 7178 (Khoa Nội tiết)",
        "https://www.bvdaihoc.com.vn/",
    ),
    "bệnh viện chợ rẫy": (
        "028 3855 4137",
        "Tổng đài đặt lịch: 1080 hoặc 028 3855 4137 (Khoa Nội tiết)",
        "https://bvchoray.vn/",
    ),
    "bệnh viện từ dũ": (
        "1900 2125",
        "Tổng đài đặt lịch khám: 1900 2125 (Tầm soát Đái tháo đường thai kỳ)",
        "https://tudu.com.vn/",
    ),
    "bệnh viện nguyễn tri phương": (
        "028 3923 4332",
        "Tổng đài đặt lịch: 028 3923 4332 (Khoa Nội tiết)",
        "https://bvnguyentriphuong.com.vn/dang-ky-kham-benh",
    ),
    "bệnh viện nhân dân 115": (
        "028 3865 2368",
        "Tổng đài CSKH & Đặt lịch: 028 3865 2368 (Khoa Nội tiết)",
        "https://benhvien115.com.vn/",
    ),
    "bệnh viện nhân dân gia định": (
        "028 3841 2692",
        "Tổng đài đặt lịch: 028 3841 2692 (Khoa Nội tiết - Thận)",
        "https://bvndgiadinh.org.vn/",
    ),
    "bệnh viện bình dân": (
        "1900 7123",
        "Tổng đài đặt lịch: 1900 7123",
        "https://bvbinhdan.com.vn/",
    ),
    "bệnh viện an bình": (
        "028 3923 4260",
        "Tổng đài CSKH: 028 3923 4260 (Khoa Nội tiết)",
        "https://benhvienanbinh.vn/",
    ),
    "bệnh viện đa khoa sài gòn": (
        "028 3829 1711",
        "Tổng đài CSKH: 028 3829 1711",
        "https://benhviendakhoasaigon.vn/",
    ),
    "bệnh viện thống nhất": (
        "028 3869 0277",
        "Tổng đài đặt lịch: 028 3869 0277 (Khoa Nội tiết)",
        "https://bvtn.org.vn/",
    ),
    "bệnh viện trưng vương": (
        "028 3865 6744",
        "Tổng đài đặt lịch: 028 3865 6744",
        "https://bvtrungvuong.vn/",
    ),
    "bệnh viện quân y 175": (
        "1900 1175",
        "Tổng đài đặt lịch khám: 1900 1175 (Khoa Nội tiết)",
        "https://benhvien175.vn/",
    ),
    "bệnh viện đa khoa tâm anh tp.hcm": (
        "028 7102 6789",
        "Hotline đặt lịch: 028 7102 6789 (Khoa Nội tiết - Đái tháo đường)",
        "https://tamanhhospital.vn/danh-cho-khach-hang/dat-lich-kham/",
    ),
    "bệnh viện fv": (
        "028 5411 3333",
        "Tổng đài đặt lịch: 028 5411 3333 (Khoa Nội tiết)",
        "https://www.fvhospital.com/vi/dat-hen/",
    ),
    "bệnh viện tim tâm đức": (
        "028 5411 0036",
        "Tổng đài đặt lịch khám: 028 5411 0036",
        "https://tamduchearthospital.com/",
    ),
    "trung tâm y khoa medic": (
        "028 3927 0284",
        "Tổng đài xét nghiệm & khám bệnh Hòa Hảo: 028 3927 0284",
        "https://medic.com.vn/",
    ),
    "bệnh viện đa khoa vạn hạnh": (
        "028 3863 2553",
        "Tổng đài đặt lịch: 028 3863 2553",
        "https://benhvienvanhanh.com/",
    ),
    "vinmec central park": (
        "028 3622 1166",
        "Tổng đài đặt lịch Vinmec Central Park: 028 3622 1166",
        "https://www.vinmec.com/vi/",
    ),
    "bệnh viện đa khoa hồng đức": (
        "028 3996 9999",
        "Tổng đài đặt lịch: 028 3996 9999",
        "https://benhvienhongduc.vn/",
    ),
    "bệnh viện hoàn mỹ sài gòn": (
        "028 3990 2468",
        "Tổng đài đặt lịch: 028 3990 2468 (Khoa Nội tiết)",
        "https://hoanmy.com/saigon/dat-lich-kham/",
    ),
    "hoàn mỹ thủ đức": (
        "028 7306 2062",
        "Tổng đài đặt lịch: 028 7306 2062 (Khoa Nội tiết)",
        "https://hoanmy.com/thuduc/dat-lich-kham/",
    ),
    "bệnh viện đa khoa khu vực thủ đức": (
        "028 3722 3556",
        "Tổng đài CSKH: 028 3722 3556 (Khoa Nội tiết)",
        "https://benhvienkhuvucthuduc.vn/",
    ),
    "bệnh viện thành phố thủ đức": (
        "028 3896 6894",
        "Tổng đài CSKH: 028 3896 6894 (Khoa Nội tiết)",
        "https://benhvienthuduc.vn/",
    ),
    "bệnh viện lê văn thịnh": (
        "028 5432 7888",
        "Tổng đài CSKH: 028 5432 7888 (Khoa Nội tiết)",
        "https://benhvienlevanthinh.vn/",
    ),
    "victoria healthcare": (
        "028 3910 4545",
        "Tổng đài đặt lịch Victoria Healthcare: 028 3910 4545",
        "https://www.victoriavn.com/",
    ),
    "careplus": (
        "1800 6116",
        "Tổng đài đặt lịch CarePlus: 1800 6116",
        "https://careplusvn.com/vi/dat-lich-hen",
    ),
    "golden healthcare": (
        "0369 03 18 18",
        "Hotline đặt lịch Golden Healthcare: 0369 03 18 18",
        "https://goldenhealthcarevn.com/",
    ),
    "diag": (
        "1900 1717",
        "Tổng đài đặt lịch xét nghiệm đường huyết & HbA1c: 1900 1717",
        "https://diag.vn/dat-lich-hen/",
    ),

    # --- BÌNH DƯƠNG & BÀ RỊA - VŨNG TÀU ---
    "bệnh viện đa khoa tỉnh bình dương": (
        "0274 3822 920",
        "Tổng đài CSKH: 0274 3822 920 (Khoa Nội tiết)",
        "https://benhvienbinhduong.org.vn/",
    ),
    "bệnh viện đa khoa quốc tế becamex": (
        "1900 2676",
        "Tổng đài đặt lịch khám: 1900 2676 (Chuyên khoa Nội tiết)",
        "https://bih.vn/dat-lich-hen/",
    ),
    "bệnh viện đa khoa medic bình dương": (
        "0274 3855 997",
        "Tổng đài đặt lịch Medic Bình Dương: 0274 3855 997",
        "https://medicbinhduong.vn/",
    ),
    "columbia asia bình dương": (
        "0274 381 9933",
        "Tổng đài đặt lịch Columbia Asia: 0274 381 9933",
        "https://www.columbiaasia.com/vietnam/",
    ),
    "bệnh viện đa khoa quốc tế hạnh phúc": (
        "1900 6765",
        "Tổng đài đặt lịch: 1900 6765",
        "https://www.hanhphuchospital.com/dat-hen/",
    ),
    "bệnh viện đa khoa mỹ phước": (
        "0274 3535 777",
        "Hotline đặt lịch: 0274 3535 777",
        "https://benhvienmyphuoc.vn/dat-lich-kham.html",
    ),
    "bệnh viện vũng tàu": (
        "0254 3832 667",
        "Tổng đài CSKH Bệnh viện Vũng Tàu: 0254 3832 667",
        "https://benhvienvungtau.vn/",
    ),
    "bệnh viện bà rịa": (
        "0254 3731 115",
        "Tổng đài CSKH Bệnh viện Bà Rịa: 0254 3731 115",
        "https://benhvienbaria.com/",
    ),

    # --- HÀ NỘI ---
    "bệnh viện bạch mai": (
        "1900 888 866",
        "Tổng đài đặt lịch khám: 1900 888 866 (Khoa Nội tiết - Đái tháo đường)",
        "https://bachmai.gov.vn/",
    ),
    "bệnh viện nội tiết trung ương": (
        "024 3853 3527",
        "Tổng đài tư vấn & đặt lịch: 024 3853 3527 (Chuyên khoa Đái tháo đường)",
        "https://benhviennoitiet.vn/",
    ),
    "bệnh viện đại học y hà nội": (
        "1900 6422",
        "Tổng đài đặt lịch khám: 1900 6422 (Khoa Nội tiết)",
        "https://benhviendaihocyhanoi.com/",
    ),
    "bệnh viện trung ương quân đội 108": (
        "1900 986 869",
        "Tổng đài đặt lịch: 1900 986 869 (Khoa Nội tiết)",
        "https://www.benhvien108.vn/dang-ky-kham-benh.htm",
    ),
    "bệnh viện hữu nghị việt đức": (
        "1900 1902",
        "Tổng đài đặt lịch: 1900 1902",
        "https://benhvienvietduc.org/",
    ),
    "bệnh viện tim hà nội": (
        "024 3942 2430",
        "Tổng đài đặt lịch Bệnh viện Tim Hà Nội: 024 3942 2430",
        "https://benhvientimhanoi.vn/",
    ),
    "bệnh viện đa khoa xanh pôn": (
        "1900 6155",
        "Tổng đài đặt lịch Bệnh viện Xanh Pôn: 1900 6155",
        "https://bvxanhpon.vn/",
    ),
    "bệnh viện thanh nhàn": (
        "024 3971 4363",
        "Tổng đài đặt lịch Bệnh viện Thanh Nhàn: 024 3971 4363",
        "https://thanhnhanhospital.vn/",
    ),
    "bệnh viện e": (
        "1900 1548",
        "Tổng đài đặt lịch Bệnh viện E: 1900 1548 (Khoa Nội tiết)",
        "https://benhviene.com/",
    ),
    "bệnh viện quân y 103": (
        "0967 811 616",
        "Tổng đài CSKH Bệnh viện Quân y 103: 0967 811 616",
        "https://benhvien103.vn/",
    ),
    "bệnh viện đa khoa đức giang": (
        "1900 292 919",
        "Tổng đài đặt lịch BVĐK Đức Giang: 1900 292 919",
        "https://benhvienducgiang.com/",
    ),
    "bệnh viện đa khoa hà đông": (
        "024 3382 4524",
        "Tổng đài CSKH BVĐK Hà Đông: 024 3382 4524",
        "https://benhvienhadong.vn/",
    ),
    "bệnh viện đa khoa tâm anh hà nội": (
        "024 7106 6858",
        "Hotline đặt lịch Tâm Anh Hà Nội: 024 7106 6858 (Khoa Nội tiết)",
        "https://tamanhhospital.vn/danh-cho-khach-hang/dat-lich-kham/",
    ),
    "vinmec times city": (
        "024 3974 3556",
        "Tổng đài đặt lịch Vinmec Times City: 024 3974 3556",
        "https://www.vinmec.com/vi/",
    ),
    "bệnh viện đa khoa hồng ngọc": (
        "024 3927 5568",
        "Tổng đài đặt lịch Hồng Ngọc: 024 3927 5568",
        "https://hongngochospital.vn/dat-lich-kham",
    ),
    "thu cúc": (
        "1900 558 892",
        "Tổng đài đặt lịch Thu Cúc TCI: 1900 558 892",
        "https://benhvienthucuc.vn/dat-lich-kham/",
    ),
    "bệnh viện đa khoa phương đông": (
        "1900 1806",
        "Tổng đài đặt lịch Phương Đông: 1900 1806",
        "https://benhvienphuongdong.vn/dat-lich-kham/",
    ),
    "bệnh viện đa khoa an việt": (
        "1900 2838",
        "Tổng đài đặt lịch An Việt: 1900 2838",
        "https://benhvienanviet.com/",
    ),

    # --- CÁC TỈNH / THÀNH PHỐ KHÁC ---
    "bệnh viện hữu nghị việt tiệp": (
        "0225 3700 436",
        "Tổng đài CSKH BV Hữu nghị Việt Tiệp (Hải Phòng): 0225 3700 436",
        "https://viettiephospital.vn/",
    ),
    "bệnh viện đa khoa tỉnh hải dương": (
        "0220 3890 205",
        "Tổng đài CSKH BVĐK Tỉnh Hải Dương: 0220 3890 205",
        "https://benhvienhaiduong.vn/",
    ),
    "bệnh viện đà nẵng": (
        "0236 3821 118",
        "Tổng đài CSKH Bệnh viện Đà Nẵng: 0236 3821 118 (Khoa Nội tiết)",
        "https://dananghospital.org.vn/",
    ),
    "bệnh viện đa khoa tỉnh quảng nam": (
        "0235 3851 429",
        "Tổng đài CSKH BVĐK Tỉnh Quảng Nam: 0235 3851 429",
        "https://bvdkquangnam.vn/",
    ),
    "bệnh viện đa khoa trung ương cần thơ": (
        "0292 3820 071",
        "Tổng đài CSKH BVĐK Trung ương Cần Thơ: 0292 3820 071 (Khoa Nội tiết)",
        "https://bvtwct.vn/",
    ),
    "bệnh viện đa khoa trung tâm an giang": (
        "0296 3852 543",
        "Tổng đài CSKH BVĐK Trung tâm An Giang: 0296 3852 543",
        "https://bvag.com.vn/",
    ),
    "bệnh viện đa khoa đồng nai": (
        "0251 8969 999",
        "Tổng đài đặt lịch BVĐK Đồng Nai: 0251 8969 999 (Khoa Nội tiết)",
        "https://benhviendakhoadongnai.com/",
    ),
    "bệnh viện đa khoa tỉnh khánh hòa": (
        "0258 3822 175",
        "Tổng đài CSKH BVĐK Tỉnh Khánh Hòa: 0258 3822 175",
        "https://benhvienkhanhhoa.org.vn/",
    ),
    "bệnh viện đa khoa tỉnh lâm đồng": (
        "0263 3822 154",
        "Tổng đài CSKH BVĐK Tỉnh Lâm Đồng: 0263 3822 154",
        "https://benhvienlamdong.vn/",
    ),
    "bệnh viện hữu nghị đa khoa nghệ an": (
        "0238 3844 528",
        "Tổng đài CSKH BV Hữu nghị Đa khoa Nghệ An: 0238 3844 528",
        "https://bvnghean.vn/",
    ),
    "bệnh viện đa khoa tỉnh quảng ninh": (
        "0203 3825 499",
        "Tổng đài CSKH BVĐK Tỉnh Quảng Ninh: 0203 3825 499",
        "https://benhviendakhoatinhquangninh.vn/",
    ),
    "bệnh viện bãi cháy": (
        "1900 969 694",
        "Tổng đài đặt lịch Bệnh viện Bãi Cháy: 1900 969 694",
        "https://benhvienbaichay.vn/",
    ),
    "bệnh viện trung ương thái nguyên": (
        "0208 3855 125",
        "Tổng đài CSKH BV Trung ương Thái Nguyên: 0208 3855 125",
        "https://bvdktuthainguyen.gov.vn/",
    ),
    "bệnh viện đa khoa tỉnh thanh hóa": (
        "0237 3951 467",
        "Tổng đài CSKH BVĐK Tỉnh Thanh Hóa: 0237 3951 467",
        "https://bvdktinhthanhhoa.com.vn/",
    ),
    "bệnh viện nguyễn đình chiểu": (
        "0275 3822 355",
        "Tổng đài CSKH BV Nguyễn Đình Chiểu (Bến Tre): 0275 3822 355",
        "https://benhviennguyendinhchieu.vn/",
    ),
    "medlatec": (
        "1900 565 656",
        "Tổng đài đặt lịch xét nghiệm đường huyết / HbA1c: 1900 565 656",
        "https://medlatec.vn/dat-lich-kham",
    ),
}

# Ưu tiên khớp khóa dài nhất trước để tránh nhầm tên gần giống
_SORTED_HOSPITAL_KEYS = sorted(CURATED_HOSPITAL_BOOKING.keys(), key=len, reverse=True)


def _clean_html(raw: str) -> str:
    """Strip leading indentation and blank lines so CommonMark never renders HTML as a code block."""
    return "\n".join(line.strip() for line in raw.splitlines() if line.strip())


def _is_en() -> bool:
    return st.session_state.get("lang", "vi") == "en"


def _to_ascii_en(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return s
    s = s.replace("Đ", "D").replace("đ", "d")
    s = re.sub(r"\bPhường\s+(\d+)\b", r"Ward \1", s)
    s = re.sub(r"\bPhường\s+([^,]+)", r"\1 Ward", s)
    s = re.sub(r"\bQuận\s+(\d+)\b", r"District \1", s)
    s = re.sub(r"\bQuận\s+([^,]+)", r"\1 District", s)
    s = re.sub(r"\bHuyện\s+([^,]+)", r"\1 District", s)
    s = re.sub(r"\bĐường\s+([^,]+)", r"\1 St.", s)
    s = s.replace("TP.HCM", "HCMC").replace("TP. Hồ Chí Minh", "Ho Chi Minh City").replace("Hà Nội", "Hanoi")
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _lookup_hospital_booking_info(
    facility_name_vi: str,
    csv_phone: str = "",
    csv_url: str = "",
) -> tuple[str, str, str]:
    """Return (dial_number, display_hotline_note, direct_official_url)."""
    clean_csv_ph = str(csv_phone or "").strip()
    clean_csv_url = str(csv_url or "").strip()
    if clean_csv_url.lower() in ("nan", "none", "null"):
        clean_csv_url = ""

    dial = ""
    note = ""
    if clean_csv_ph and clean_csv_ph.lower() not in ("nan", "none", "null", ""):
        dial = re.sub(r"[^\d+]", "", clean_csv_ph)
        note = clean_csv_ph

    norm = str(facility_name_vi or "").strip().lower()
    matched_url = clean_csv_url
    for key in _SORTED_HOSPITAL_KEYS:
        if key in norm:
            c_dial, c_note, c_url = CURATED_HOSPITAL_BOOKING[key]
            if not dial:
                dial = re.sub(r"[^\d+]", "", c_dial)
                note = c_note
            if not matched_url:
                matched_url = c_url
            break

    return dial, note, matched_url


@st.cache_data(ttl=3600, show_spinner=False)
def lookup_osm_contact_by_coord(lat: float, lon: float) -> tuple[str, str]:
    """Query OpenStreetMap Overpass around exact hospital coordinates to fetch phone & official website."""
    try:
        q = f"""
        [out:json][timeout:6];
        (
          node["amenity"~"hospital|clinic"](around:400,{lat},{lon});
          way["amenity"~"hospital|clinic"](around:400,{lat},{lon});
          relation["amenity"~"hospital|clinic"](around:400,{lat},{lon});
        );
        out tags 8;
        """
        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": q},
            headers=HEADERS,
            timeout=6,
        )
        if resp.status_code == 200:
            found_ph = ""
            found_web = ""
            for el in resp.json().get("elements", []):
                tags = el.get("tags", {})
                if not found_ph:
                    ph = tags.get("phone") or tags.get("contact:phone") or tags.get("telephone") or ""
                    if ph.strip():
                        found_ph = ph.strip()
                if not found_web:
                    web = tags.get("website") or tags.get("contact:website") or tags.get("url") or ""
                    if web.strip().startswith("http"):
                        found_web = web.strip()
            return found_ph, found_web
    except Exception:
        pass
    return "", ""


# Crisp inline SVG icons
SVG_PIN = (
    '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#1D4ED8" '
    'stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 18px;">'
    '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>'
    '<circle cx="12" cy="10" r="3"/>'
    '</svg>'
)

SVG_PIN_SM = (
    '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#5B6B82" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 14px;margin-top:2px;">'
    '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>'
    '<circle cx="12" cy="10" r="3"/>'
    '</svg>'
)

SVG_HOSPITAL = (
    '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="#1D4ED8" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 15px;">'
    '<path d="M12 6v4"/><path d="M14 14h-4"/><path d="M14 18h-4"/><path d="M14 8h-4"/>'
    '<path d="M18 12h2a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2h2"/>'
    '<path d="M18 22V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v18"/>'
    '</svg>'
)

SVG_CLINIC = (
    '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="#16A34A" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 15px;">'
    '<path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"/>'
    '<path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"/>'
    '<circle cx="20" cy="10" r="2"/>'
    '</svg>'
)

SVG_STAR = (
    '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#B45309" '
    'stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 14px;">'
    '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>'
    '</svg>'
)

SVG_LAB = (
    '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="#0F766E" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 13px;margin-top:2px;">'
    '<path d="M9 3h6"/><path d="M10 9h4"/><path d="M10 3v6L5 20a1 1 0 0 0 .9 1.5h12.2a1 1 0 0 0 .9-1.5L14 9V3"/>'
    '</svg>'
)

SVG_PHONE = (
    '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#047857" '
    'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 14px;margin-top:1px;">'
    '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 '
    '19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 '
    '2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>'
    '</svg>'
)

SVG_PHONE_WHITE = (
    '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="#FFFFFF" '
    'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 13px;">'
    '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 '
    '19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 '
    '2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>'
    '</svg>'
)

SVG_CALENDAR = (
    '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="#1D4ED8" '
    'stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 13px;">'
    '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>'
    '<line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>'
    '<line x1="3" y1="10" x2="21" y2="10"/>'
    '</svg>'
)

SVG_NAV_ARROW = (
    '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#FFFFFF" '
    'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 14px;">'
    '<polygon points="3 11 22 2 13 21 11 13 3 11"/>'
    '</svg>'
)

SVG_MAP_HEADER = (
    '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#142D4E" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 16px;">'
    '<polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/>'
    '<line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/>'
    '</svg>'
)


@st.cache_data(show_spinner=False)
def load_clinics_csv() -> pd.DataFrame:
    """Load the hierarchical Province/City -> District/County diabetes testing facilities CSV."""
    if PROVINCES_CSV_PATH.exists():
        df = pd.read_csv(PROVINCES_CSV_PATH, encoding="utf-8-sig")
        for col in [
            "Tinh_Thanh_Moi",
            "Tinh_Thanh_Moi_EN",
            "Nhan_Hien_Thi",
            "Nhan_Hien_Thi_EN",
            "Tinh_Cu_Sap_Nhap",
            "Quan_Huyen",
            "Quan_Huyen_EN",
            "Ten_Benh_Vien",
            "Ten_Benh_Vien_EN",
            "Dia_Chi",
            "Dia_Chi_EN",
            "Loai_Co_So",
            "Loai_Co_So_EN",
            "Dich_Vu_Xet_Nghiem",
            "Dich_Vu_Xet_Nghiem_EN",
            "Tu_Khoa_Google_Maps",
            "Hotline",
            "So_Dien_Thoai",
            "SDT",
            "Website",
            "Link_Dat_Lich",
        ]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()
        return df
    return pd.DataFrame()


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@st.cache_data(ttl=3600, show_spinner=False)
def geocode_location(query: str) -> tuple[float, float, str] | None:
    """Resolve province/district/city into real (lat, lon) via Nominatim."""
    q_clean = query.strip()
    if not q_clean:
        return None
    search_q = q_clean if "vietnam" in q_clean.lower() or "việt nam" in q_clean.lower() else f"{q_clean}, Vietnam"
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": search_q, "format": "json", "limit": 1, "accept-language": "vi,en"},
            headers=HEADERS,
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"]), str(data[0].get("display_name", q_clean))
    except Exception:
        pass
    return None


@st.cache_data(ttl=1800, show_spinner=False)
def retrieve_real_clinics(lat: float, lon: float, radius_m: int = 5000, prefer_en: bool = False) -> list[dict]:
    """Retrieve additional nearby hospitals and clinics around (lat, lon) from OpenStreetMap Overpass API."""
    overpass_query = f"""
    [out:json][timeout:10];
    (
      node["amenity"~"hospital|clinic"](around:{radius_m},{lat},{lon});
      way["amenity"~"hospital|clinic"](around:{radius_m},{lat},{lon});
      node["healthcare"~"hospital|clinic|laboratory"](around:{radius_m},{lat},{lon});
    );
    out center 25;
    """
    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]
    elements = []
    for url in endpoints:
        try:
            resp = requests.post(
                url,
                data={"data": overpass_query},
                headers=HEADERS,
                timeout=10,
            )
            if resp.status_code == 200:
                elements = resp.json().get("elements", [])
                if elements:
                    break
        except Exception:
            continue

    results = []
    seen = set()
    for el in elements:
        tags = el.get("tags", {})
        if prefer_en:
            raw_name = tags.get("name:en") or tags.get("int_name") or tags.get("name") or tags.get("official_name")
            name = _to_ascii_en(raw_name) if raw_name else None
        else:
            name = tags.get("name:vi") or tags.get("name") or tags.get("official_name")
        if not name:
            continue
        norm_name = name.strip().lower()
        if norm_name in seen:
            continue
        seen.add(norm_name)

        c_lat = el.get("lat") if "lat" in el else el.get("center", {}).get("lat")
        c_lon = el.get("lon") if "lon" in el else el.get("center", {}).get("lon")
        if c_lat is None or c_lon is None:
            continue

        amenity = tags.get("amenity") or tags.get("healthcare") or "clinic"
        is_hospital = amenity == "hospital"

        housenumber = tags.get("addr:housenumber", "")
        street = tags.get("addr:street", "")
        ward = tags.get("addr:suburb", "") or tags.get("addr:quarter", "")
        district = tags.get("addr:district", "") or tags.get("addr:city", "") or tags.get("addr:province", "")
        street_line = " ".join(p for p in [housenumber, street] if p)
        full_addr = tags.get("addr:full") or ", ".join(p for p in [street_line, ward, district] if p)
        if prefer_en and full_addr:
            full_addr = _to_ascii_en(full_addr)

        phone = tags.get("phone") or tags.get("contact:phone") or ""
        website = tags.get("website") or tags.get("contact:website") or ""
        dist_km = _haversine_km(lat, lon, float(c_lat), float(c_lon))

        results.append(
            {
                "name": name.strip(),
                "is_hospital": is_hospital,
                "address": full_addr,
                "phone": phone.strip(),
                "website": website.strip(),
                "distance_km": round(dist_km, 2),
                "lat": float(c_lat),
                "lon": float(c_lon),
            }
        )

    results.sort(key=lambda x: x["distance_km"])
    return results[:8]


def _clean_district_for_geocode(district_label: str) -> str:
    """Strip parenthetical old-province hints like '(Bình Dương cũ)' so Nominatim geocodes cleanly."""
    return re.sub(r"\s*\([^)]*\)", "", district_label).strip()


def _render_facility_card(
    name: str,
    name_vi_raw: str,
    address: str,
    badge_cls: str,
    badge_svg: str,
    badge_txt: str,
    right_pill: str,
    maps_query: str,
    service_txt: str = "",
    phone: str = "",
    website_url: str = "",
    lat: float | None = None,
    lon: float | None = None,
):
    q_maps = urllib.parse.quote(maps_query)
    maps_url = f"https://www.google.com/maps/search/?api=1&query={q_maps}"
    cta_maps = tr("Chỉ đường trên Google Maps", "Directions on Google Maps")

    # Resolve hotline + official hospital website URL
    dial_num, hotline_note, direct_url = _lookup_hospital_booking_info(
        name_vi_raw or name, phone, website_url
    )
    if (not dial_num or not direct_url) and lat is not None and lon is not None:
        osm_ph, osm_web = lookup_osm_contact_by_coord(float(lat), float(lon))
        if not dial_num and osm_ph:
            dial_num = re.sub(r"[^\d+]", "", osm_ph)
            hotline_note = osm_ph
        if not direct_url and osm_web:
            direct_url = osm_web

    if dial_num:
        if _is_en():
            hotline_label = f"Endocrinology / Glucose Booking Hotline: <strong>{hotline_note}</strong>"
        else:
            hotline_label = f"Hotline đặt lịch Khoa Nội tiết / Đường huyết: <strong>{hotline_note}</strong>"
        hotline_box_html = (
            f'<div class="gg-cf-hotline">'
            f'{SVG_PHONE}<span>{hotline_label}</span>'
            f'</div>'
        )
        call_btn_html = (
            f'<a class="gg-cf-btn-call" href="tel:{dial_num}">'
            f'{SVG_PHONE_WHITE}<span>{tr("Gọi đặt lịch", "Call to Book")} ({dial_num})</span>'
            f'</a>'
        )
    else:
        hotline_box_html = (
            f'<div class="gg-cf-hotline gg-cf-hotline-muted">'
            f'{SVG_PHONE}<span>{tr("Liên hệ quầy tiếp nhận / cổng thông tin bệnh viện để đăng ký khám Khoa Nội tiết & xét nghiệm đường huyết:", "Contact the hospital reception or official portal to book Endocrinology & blood glucose testing:")}</span>'
            f'</div>'
        )
        call_btn_html = ""

    if direct_url:
        website_btn_html = (
            f'<a class="gg-cf-btn-sec" href="{direct_url}" target="_blank" rel="noopener noreferrer">'
            f'{SVG_CALENDAR}<span>{tr("Đặt lịch / Trang chính thức Bệnh viện ↗", "Official Hospital Portal ↗")}</span>'
            f'</a>'
        )
    else:
        website_btn_html = ""

    service_html = (
        f'<div class="gg-cf-svc">{SVG_LAB}<span>{service_txt}</span></div>'
        if service_txt
        else ""
    )

    card_html = _clean_html(
        f"""
        <div class="gg-cf-card">
            <div class="gg-cf-top-row">
                <span class="{badge_cls}">{badge_svg}<span>{badge_txt}</span></span>
                <span class="gg-cf-dist">{right_pill}</span>
            </div>
            <div class="gg-cf-name">{name}</div>
            <div class="gg-cf-meta">{SVG_PIN_SM}<span>{address}</span></div>
            {service_html}
            {hotline_box_html}
            <div class="gg-cf-actions">
                {call_btn_html}
                {website_btn_html}
                <a class="gg-cf-btn" href="{maps_url}" target="_blank" rel="noopener noreferrer">
                    {SVG_NAV_ARROW}<span>{cta_maps}</span>
                </a>
            </div>
        </div>
        """
    )
    st.markdown(card_html, unsafe_allow_html=True)


def render_clinic_finder():
    """Render hierarchical Province/City -> District/County selector reading directly from data/provinces_34.csv."""
    is_en = _is_en()
    st.markdown(
        _clean_html(
            """
            <style>
            .gg-cf-head {
                display: flex;
                align-items: flex-start;
                gap: 10px;
                margin-bottom: 10px;
            }
            .gg-cf-title {
                font-size: 1.08rem;
                font-weight: 800;
                color: #142D4E;
                line-height: 1.3;
                margin: 0;
            }
            .gg-cf-sub {
                font-size: 0.85rem;
                color: #5B6B82;
                margin: 3px 0 0 0;
                line-height: 1.45;
            }
            .gg-cf-card {
                background: #F8FAFC;
                border: 1px solid #E2EAF4;
                border-radius: 12px;
                padding: 13px 15px;
                margin-bottom: 10px;
                transition: border-color 0.15s ease, box-shadow 0.15s ease;
            }
            .gg-cf-card:hover {
                border-color: #BFDBFE;
                box-shadow: 0 3px 10px rgba(29, 78, 216, 0.06);
            }
            .gg-cf-top-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 8px;
                margin-bottom: 6px;
                flex-wrap: wrap;
            }
            .gg-cf-badge-hosp {
                display: inline-flex;
                align-items: center;
                gap: 5px;
                background: #EFF6FF;
                color: #1D4ED8;
                border: 1px solid #BFDBFE;
                border-radius: 999px;
                padding: 2px 9px;
                font-size: 0.74rem;
                font-weight: 700;
            }
            .gg-cf-badge-clin {
                display: inline-flex;
                align-items: center;
                gap: 5px;
                background: #F0FDF4;
                color: #15803D;
                border: 1px solid #BBF7D0;
                border-radius: 999px;
                padding: 2px 9px;
                font-size: 0.74rem;
                font-weight: 700;
            }
            .gg-cf-badge-ref {
                display: inline-flex;
                align-items: center;
                gap: 5px;
                background: #FFFBEB;
                color: #B45309;
                border: 1px solid #FDE68A;
                border-radius: 999px;
                padding: 2px 9px;
                font-size: 0.74rem;
                font-weight: 700;
            }
            .gg-cf-dist {
                font-size: 0.75rem;
                font-weight: 700;
                color: #475569;
                background: #FFFFFF;
                border: 1px solid #DCE5F2;
                border-radius: 999px;
                padding: 2px 9px;
            }
            .gg-cf-name {
                font-size: 0.95rem;
                font-weight: 700;
                color: #142D4E;
                margin-bottom: 5px;
                line-height: 1.35;
            }
            .gg-cf-meta {
                display: flex;
                align-items: flex-start;
                gap: 6px;
                font-size: 0.82rem;
                color: #5B6B82;
                margin-bottom: 4px;
                line-height: 1.4;
            }
            .gg-cf-svc {
                display: flex;
                align-items: flex-start;
                gap: 6px;
                font-size: 0.81rem;
                color: #0F766E;
                font-weight: 500;
                margin-bottom: 5px;
                line-height: 1.4;
            }
            .gg-cf-hotline {
                display: flex;
                align-items: flex-start;
                gap: 6px;
                background: #ECFDF5;
                border: 1px solid #A7F3D0;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 0.80rem;
                color: #065F46;
                margin: 5px 0 4px 0;
                line-height: 1.4;
            }
            .gg-cf-hotline-muted {
                background: #F1F5F9;
                border-color: #CBD5E1;
                color: #334155;
            }
            .gg-cf-actions {
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 7px;
                margin-top: 8px;
            }
            .gg-cf-btn {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                background: #1D4ED8;
                color: #FFFFFF !important;
                text-decoration: none !important;
                font-size: 0.79rem;
                font-weight: 600;
                padding: 6px 12px;
                border-radius: 9px;
                transition: background 0.15s ease;
            }
            .gg-cf-btn:hover {
                background: #1E40AF;
            }
            .gg-cf-btn-call {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                background: #059669;
                color: #FFFFFF !important;
                text-decoration: none !important;
                font-size: 0.79rem;
                font-weight: 700;
                padding: 6px 12px;
                border-radius: 9px;
                transition: background 0.15s ease;
            }
            .gg-cf-btn-call:hover {
                background: #047857;
            }
            .gg-cf-btn-sec {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                background: #FFFFFF;
                color: #1D4ED8 !important;
                border: 1px solid #BFDBFE;
                text-decoration: none !important;
                font-size: 0.79rem;
                font-weight: 600;
                padding: 5px 11px;
                border-radius: 9px;
                transition: background 0.15s ease;
            }
            .gg-cf-btn-sec:hover {
                background: #EFF6FF;
            }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )

    df_csv = load_clinics_csv()

    with st.container(border=True):
        c_head, c_gps = st.columns([3.05, 1.4], vertical_alignment="center")
        with c_head:
            st.markdown(
                _clean_html(
                    f"""
                    <div class="gg-cf-head">
                        <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;padding:8px;display:flex;align-items:center;justify-content:center;">
                            {SVG_PIN}
                        </div>
                        <div>
                            <div class="gg-cf-title">{tr("Tìm cơ sở xét nghiệm tiểu đường & Đặt lịch khám Nội tiết", "Find Diabetes Testing Facilities & Book Endocrinology Visit")}</div>
                            <p class="gg-cf-sub">{tr(
                                "Chọn theo từng cấp: 1) Tỉnh / Thành phố → 2) Quận / Huyện / Thành phố để xem danh sách bệnh viện, số Hotline & trang chính thức của bệnh viện.",
                                "Filter by: 1) Province / City → 2) District / County to view hospitals, booking hotlines, and official hospital portals."
                            )}</p>
                        </div>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

        if not df_csv.empty:
            prov_cols = ["ID", "Tinh_Thanh_Moi", "Tinh_Thanh_Moi_EN", "Nhan_Hien_Thi", "Nhan_Hien_Thi_EN"]
            avail_cols = [c for c in prov_cols if c in df_csv.columns]
            prov_df = df_csv[avail_cols].drop_duplicates(subset=["ID"]).sort_values("ID")
            id_to_row = {int(r["ID"]): r for _, r in prov_df.iterrows()}
            prov_ids = list(id_to_row.keys())
        else:
            id_to_row = {
                1: {
                    "Tinh_Thanh_Moi": "TP. Hồ Chí Minh",
                    "Tinh_Thanh_Moi_EN": "Ho Chi Minh City",
                    "Nhan_Hien_Thi": "TP. Hồ Chí Minh",
                    "Nhan_Hien_Thi_EN": "Ho Chi Minh City",
                }
            }
            prov_ids = [1]

        def _fmt_prov(pid: int) -> str:
            r = id_to_row[pid]
            if is_en:
                return r.get("Nhan_Hien_Thi_EN") or _to_ascii_en(r.get("Nhan_Hien_Thi", ""))
            return r.get("Nhan_Hien_Thi", "")

        c_prov, c_dist, c_rad = st.columns([2.15, 1.65, 0.9])
        with c_prov:
            prov_id = st.selectbox(
                tr("1. Tỉnh / Thành phố:", "1. Province / City:"),
                options=prov_ids,
                index=0,
                format_func=_fmt_prov,
                key="gg_clinic_province_34",
            )
            prov_meta = id_to_row[prov_id]
            prov_name_vi = prov_meta["Tinh_Thanh_Moi"]
            prov_name_en = prov_meta.get("Tinh_Thanh_Moi_EN") or _to_ascii_en(prov_name_vi)
            prov_display = prov_name_en if is_en else prov_name_vi

        sub_df = df_csv[df_csv["Tinh_Thanh_Moi"] == prov_name_vi] if not df_csv.empty else pd.DataFrame()
        if not sub_df.empty:
            dist_vi_list = list(dict.fromkeys(sub_df["Quan_Huyen"].tolist()))
            vi_to_en_dist = {}
            for _, r in sub_df.iterrows():
                d_vi = r["Quan_Huyen"]
                if d_vi not in vi_to_en_dist:
                    vi_to_en_dist[d_vi] = r.get("Quan_Huyen_EN") or _to_ascii_en(d_vi)
        else:
            dist_vi_list = ["Quận 1"]
            vi_to_en_dist = {"Quận 1": "District 1"}

        ALL_TOKEN = "__ALL__"
        CUSTOM_TOKEN = "__CUSTOM__"
        district_choices = dist_vi_list + [ALL_TOKEN, CUSTOM_TOKEN]

        def _fmt_dist(token: str) -> str:
            if token == ALL_TOKEN:
                return tr("— Tất cả quận/huyện trong tỉnh/thành —", "— All districts in province/city —")
            if token == CUSTOM_TOKEN:
                return tr("Khác (tự nhập tên quận/huyện/phường)...", "Other (type district/ward)...")
            return vi_to_en_dist.get(token, _to_ascii_en(token)) if is_en else token

        with c_dist:
            selected_dist = st.selectbox(
                tr("2. Quận / Huyện / Thành phố:", "2. District / County / City:"),
                options=district_choices,
                index=0,
                format_func=_fmt_dist,
                key=f"gg_clinic_dist_{prov_id}",
            )

        with c_rad:
            radius_km = st.selectbox(
                tr("Bán kính:", "Radius:"),
                options=[3, 5, 10, 15],
                index=1,
                format_func=lambda x: f"{x} km",
                key="gg_clinic_radius_select",
            )

        sub_clean_vi = ""
        sub_clean_disp = ""
        is_custom_input = False
        if selected_dist == CUSTOM_TOKEN:
            is_custom_input = True
            custom_txt = st.text_input(
                tr("Nhập tên Quận / Huyện / Phường / Đường:", "Enter District / Ward / Street:"),
                value="",
                placeholder=tr("VD: Quận 1, Phường Bến Thành...", "e.g., District 1, Ben Thanh Ward..."),
                key=f"gg_clinic_custom_sub_{prov_id}",
            )
            sub_clean_vi = custom_txt.strip()
            sub_clean_disp = sub_clean_vi
        elif selected_dist != ALL_TOKEN:
            sub_clean_vi = selected_dist
            sub_clean_disp = vi_to_en_dist.get(selected_dist, _to_ascii_en(selected_dist)) if is_en else selected_dist

        if not sub_df.empty:
            if selected_dist == ALL_TOKEN:
                matched_csv = sub_df.copy()
            elif is_custom_input:
                if sub_clean_vi:
                    kw = sub_clean_vi.lower()
                    mask = (
                        sub_df["Quan_Huyen"].str.lower().str.contains(kw, regex=False)
                        | sub_df["Dia_Chi"].str.lower().str.contains(kw, regex=False)
                        | sub_df["Ten_Benh_Vien"].str.lower().str.contains(kw, regex=False)
                    )
                    if "Quan_Huyen_EN" in sub_df.columns:
                        mask = mask | sub_df["Quan_Huyen_EN"].str.lower().str.contains(kw, regex=False)
                    if "Dia_Chi_EN" in sub_df.columns:
                        mask = mask | sub_df["Dia_Chi_EN"].str.lower().str.contains(kw, regex=False)
                    if "Ten_Benh_Vien_EN" in sub_df.columns:
                        mask = mask | sub_df["Ten_Benh_Vien_EN"].str.lower().str.contains(kw, regex=False)
                    matched_csv = sub_df[mask].copy()
                else:
                    matched_csv = sub_df.copy()
            else:
                matched_csv = sub_df[sub_df["Quan_Huyen"] == sub_clean_vi].copy()
        else:
            matched_csv = pd.DataFrame()

        geocode_sub = _clean_district_for_geocode(sub_clean_vi) if sub_clean_vi else ""
        effective_query_vi = f"{geocode_sub}, {prov_name_vi}" if geocode_sub else prov_name_vi
        effective_query_disp = (
            f"{_clean_district_for_geocode(sub_clean_disp)}, {prov_display}"
            if sub_clean_disp
            else prov_display
        )
        display_area = f"{sub_clean_disp} · {prov_display}" if sub_clean_disp else prov_display

        maps_search_q = urllib.parse.quote(
            f"diabetes testing hospital clinic {effective_query_disp}"
            if is_en
            else f"xét nghiệm tiểu đường bệnh viện phòng khám {effective_query_vi}"
        )
        with c_gps:
            st.link_button(
                tr("Mở Google Maps khu vực ↗", "Open Area in Google Maps ↗"),
                url=f"https://www.google.com/maps/search/{maps_search_q}",
                type="primary",
                use_container_width=True,
            )

        map_points = []
        center_lat, center_lon = None, None
        if not matched_csv.empty and "Lat" in matched_csv.columns and "Lon" in matched_csv.columns:
            valid_coords = matched_csv.dropna(subset=["Lat", "Lon"])
            if not valid_coords.empty:
                center_lat = float(valid_coords.iloc[0]["Lat"])
                center_lon = float(valid_coords.iloc[0]["Lon"])
                for _, r in valid_coords.iterrows():
                    map_points.append({"lat": float(r["Lat"]), "lon": float(r["Lon"])})

        if center_lat is None or center_lon is None:
            geo = geocode_location(effective_query_vi)
            if geo:
                center_lat, center_lon, _ = geo
                map_points.append({"lat": center_lat, "lon": center_lon})

        extra_clinics = []
        if (is_custom_input or matched_csv.empty) and center_lat is not None and center_lon is not None:
            extra_clinics = retrieve_real_clinics(
                center_lat, center_lon, radius_m=radius_km * 1000, prefer_en=is_en
            )
            for item in extra_clinics:
                map_points.append({"lat": item["lat"], "lon": item["lon"]})

        total_found = len(matched_csv) + len(extra_clinics)
        st.caption(
            tr(
                f"Khu vực đang lọc: {display_area} — Tìm thấy {total_found} cơ sở xét nghiệm tiểu đường & nội tiết phù hợp.",
                f"Filtered area: {display_area} — Found {total_found} matching diabetes & endocrinology testing facilities.",
            )
        )

        col_list, col_map = st.columns([1.28, 1], gap="medium")
        with col_list:
            if not matched_csv.empty:
                section_lbl = (
                    tr(
                        f"Danh sách cơ sở xét nghiệm tiểu đường tại {sub_clean_disp}",
                        f"Diabetes Testing Facilities in {sub_clean_disp}",
                    )
                    if sub_clean_disp
                    else tr(
                        f"Danh sách cơ sở xét nghiệm tiểu đường tại {prov_display}",
                        f"Diabetes Testing Facilities in {prov_display}",
                    )
                )
                st.markdown(
                    _clean_html(
                        f'<div style="font-size:0.86rem;font-weight:700;color:#142D4E;margin:2px 0 7px 0;">{section_lbl}</div>'
                    ),
                    unsafe_allow_html=True,
                )
                show_df = matched_csv.head(15) if selected_dist == ALL_TOKEN else matched_csv
                for _, row in show_df.iterrows():
                    loai_vi = row.get("Loai_Co_So", "")
                    if "Bệnh viện" in loai_vi:
                        badge_cls = "gg-cf-badge-hosp"
                        badge_svg = SVG_HOSPITAL
                    elif "Xét nghiệm" in loai_vi:
                        badge_cls = "gg-cf-badge-ref"
                        badge_svg = SVG_STAR
                    else:
                        badge_cls = "gg-cf-badge-clin"
                        badge_svg = SVG_CLINIC

                    csv_phone = (
                        row.get("Hotline")
                        or row.get("So_Dien_Thoai")
                        or row.get("SDT")
                        or ""
                    )
                    csv_web = row.get("Link_Dat_Lich") or row.get("Website") or ""
                    r_lat = float(row["Lat"]) if "Lat" in row and pd.notna(row["Lat"]) else None
                    r_lon = float(row["Lon"]) if "Lon" in row and pd.notna(row["Lon"]) else None

                    if is_en:
                        badge_txt = row.get("Loai_Co_So_EN") or "Diabetes Testing Facility"
                        fac_name = row.get("Ten_Benh_Vien_EN") or _to_ascii_en(row["Ten_Benh_Vien"])
                        fac_addr = row.get("Dia_Chi_EN") or _to_ascii_en(row["Dia_Chi"])
                        fac_svc = row.get("Dich_Vu_Xet_Nghiem_EN") or "Endocrinology & Diabetes consultation, blood glucose & HbA1c testing"
                        right_pill = row.get("Quan_Huyen_EN") or _to_ascii_en(row.get("Quan_Huyen", "")) or prov_display
                    else:
                        badge_txt = loai_vi or "Cơ sở xét nghiệm tiểu đường"
                        fac_name = row["Ten_Benh_Vien"]
                        fac_addr = row["Dia_Chi"]
                        fac_svc = row.get("Dich_Vu_Xet_Nghiem", "")
                        right_pill = row.get("Quan_Huyen", "") or prov_display

                    _render_facility_card(
                        name=fac_name,
                        name_vi_raw=row["Ten_Benh_Vien"],
                        address=fac_addr,
                        badge_cls=badge_cls,
                        badge_svg=badge_svg,
                        badge_txt=badge_txt,
                        right_pill=right_pill,
                        maps_query=f"{fac_name}, {fac_addr}",
                        service_txt=fac_svc,
                        phone=csv_phone,
                        website_url=csv_web,
                        lat=r_lat,
                        lon=r_lon,
                    )

            if extra_clinics:
                st.markdown(
                    _clean_html(
                        f'<div style="font-size:0.86rem;font-weight:700;color:#142D4E;margin:10px 0 7px 0;">'
                        f'{tr(f"Cơ sở y tế lân cận quanh {effective_query_disp}", f"Nearby Facilities around {effective_query_disp}")}'
                        f'</div>'
                    ),
                    unsafe_allow_html=True,
                )
                for item in extra_clinics[:5]:
                    badge_cls = "gg-cf-badge-hosp" if item["is_hospital"] else "gg-cf-badge-clin"
                    badge_svg = SVG_HOSPITAL if item["is_hospital"] else SVG_CLINIC
                    badge_txt = (
                        tr("Bệnh viện", "Hospital")
                        if item["is_hospital"]
                        else tr("Phòng khám / Cơ sở y tế", "Clinic / Medical Facility")
                    )
                    dist_txt = tr(f"Cách ~{item['distance_km']} km", f"~{item['distance_km']} km away")
                    addr_txt = item["address"] or tr("Xem vị trí chính xác trên Google Maps", "View exact pin on Google Maps")
                    _render_facility_card(
                        name=item["name"],
                        name_vi_raw=item["name"],
                        address=addr_txt,
                        badge_cls=badge_cls,
                        badge_svg=badge_svg,
                        badge_txt=badge_txt,
                        right_pill=dist_txt,
                        maps_query=f"{item['name']}, {effective_query_disp}",
                        phone=item["phone"],
                        website_url=item.get("website", ""),
                        lat=item["lat"],
                        lon=item["lon"],
                    )

            if matched_csv.empty and not extra_clinics:
                st.info(
                    tr(
                        f"Không tìm thấy cơ sở khớp trực tiếp với '{sub_clean_disp}'. Bạn có thể chọn quận/huyện trong danh sách hoặc bấm 'Mở Google Maps khu vực ↗'.",
                        f"No direct match for '{sub_clean_disp}'. Select a district from the dropdown or click 'Open Area in Google Maps ↗'.",
                    )
                )

        with col_map:
            st.markdown(
                _clean_html(
                    f'<div style="display:flex;align-items:center;gap:6px;font-size:0.92rem;font-weight:700;color:#142D4E;margin-bottom:8px;">'
                    f'{SVG_MAP_HEADER}'
                    f'<span>{tr("Bản đồ phân bố cơ sở y tế", "Healthcare Facility Distribution Map")}</span>'
                    f'</div>'
                ),
                unsafe_allow_html=True,
            )
            if map_points:
                df_map = pd.DataFrame(map_points).drop_duplicates()
                try:
                    import pydeck as pdk

                    layer = pdk.Layer(
                        "ScatterplotLayer",
                        data=df_map,
                        get_position=["lon", "lat"],
                        get_color=[239, 68, 68, 220],
                        get_radius=120,
                        pickable=False,
                    )
                    view_state = pdk.ViewState(
                        latitude=float(df_map["lat"].mean()),
                        longitude=float(df_map["lon"].mean()),
                        zoom=12,
                    )
                    st.pydeck_chart(
                        pdk.Deck(
                            map_style=pdk.map_styles.CARTO_LIGHT,
                            initial_view_state=view_state,
                            layers=[layer],
                        ),
                        use_container_width=True,
                    )
                except Exception:
                    st.map(df_map[["lat", "lon"]], color="#EF4444", size=65, use_container_width=True)
            else:
                st.info(
                    tr(
                        "Nhấn nút 'Mở Google Maps khu vực ↗' ở góc trên để xem bản đồ trực tiếp.",
                        "Click 'Open Area in Google Maps ↗' above to view the live map.",
                    )
                )
