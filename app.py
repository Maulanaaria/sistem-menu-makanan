import streamlit as st
import pandas as pd

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity

from itertools import combinations

# =====================
# LOAD DATA
# =====================

@st.cache_data
def load_data():

    makanan = pd.read_excel(
        "data_makanan.xlsx",
        sheet_name="Menu"
    )

    # hapus kolom kosong
    makanan = makanan.dropna(
        axis=1,
        how="all"
    )

    # hapus baris kosong
    makanan = makanan.dropna(
        how="all"
    )

    # ambil kolom yang dibutuhkan
    makanan = makanan[
        [
            "Nama Menu",
            "Kalori (kkal)",
            "Protein (g)",
            "Lemak (g)",
            "Karbohidrat (g)"
        ]
    ]

    # rename kolom
    makanan.columns = [
        "nama_menu",
        "kalori",
        "protein",
        "lemak",
        "karbohidrat"
    ]

    # pastikan numerik
    for col in [
        "kalori",
        "protein",
        "lemak",
        "karbohidrat"
    ]:

        makanan[col] = pd.to_numeric(
            makanan[col],
            errors="coerce"
        )

    makanan = makanan.dropna()

    return makanan


makanan = load_data()

# =====================
# HITUNG BMR
# =====================

def hitung_bmr(
    usia,
    jk,
    bb,
    tb
):

    if jk == "L":

        return (
            (10 * bb)
            +
            (6.25 * tb)
            -
            (5 * usia)
            +
            5
        )

    else:

        return (
            (10 * bb)
            +
            (6.25 * tb)
            -
            (5 * usia)
            -
            161
        )

# =====================
# FAKTOR AKTIVITAS
# =====================

faktor_aktivitas = {

    "Ringan": 1.375,

    "Sedang": 1.55,

    "Berat": 1.725

}

# =====================
# CARI KANDIDAT MENU
# =====================

def kandidat_menu(
    target_kalori
):

    target_protein = (
        target_kalori * 0.15
    ) / 4

    target_lemak = (
        target_kalori * 0.25
    ) / 9

    target_karbohidrat = (
        target_kalori * 0.60
    ) / 4

    fitur = [
        "protein",
        "lemak",
        "karbohidrat"
    ]

    scaler = MinMaxScaler()

    data_scaled = scaler.fit_transform(
        makanan[fitur]
    )

    profil_user = [[

        target_protein,

        target_lemak,

        target_karbohidrat

    ]]

    profil_scaled = scaler.transform(
        profil_user
    )

    similarity = cosine_similarity(
        profil_scaled,
        data_scaled
    )

    hasil = makanan.copy()

    hasil["Similarity"] = similarity.flatten()

    return hasil.sort_values(
        by="Similarity",
        ascending=False
    ).head(20)

# =====================
# BENTUK PAKET MENU
# =====================

def buat_paket(
    kandidat,
    target_kalori
):

    hasil = []

    for combo in combinations(
        kandidat.index,
        3
    ):

        paket = kandidat.loc[
            list(combo)
        ]

        total_kalori = paket[
            "kalori"
        ].sum()

        rata_similarity = paket[
            "Similarity"
        ].mean()

        selisih = abs(
            target_kalori
            -
            total_kalori
        )

        hasil.append({

            "Menu 1":
            paket.iloc[0]["nama_menu"],

            "Menu 2":
            paket.iloc[1]["nama_menu"],

            "Menu 3":
            paket.iloc[2]["nama_menu"],

            "Total Kalori":
            round(
                total_kalori,
                2
            ),

            "Similarity":
            round(
                rata_similarity,
                4
            ),

            "Selisih":
            round(
                selisih,
                2
            )

        })

    hasil = pd.DataFrame(
        hasil
    )

    hasil = hasil.sort_values(
        by=[
            "Selisih",
            "Similarity"
        ],
        ascending=[
            True,
            False
        ]
    )

    return hasil.head(5)

# =====================
# REKOMENDASI
# =====================

def rekomendasi(
    usia,
    jenis_kelamin,
    berat_badan,
    tinggi_badan,
    aktivitas
):

    bmr = hitung_bmr(
        usia,
        jenis_kelamin,
        berat_badan,
        tinggi_badan
    )

    tdee = (
        bmr
        *
        faktor_aktivitas[
            aktivitas
        ]
    )

    target_kalori = (
        tdee / 3
    )

    kandidat = kandidat_menu(
        target_kalori
    )

    paket = buat_paket(
        kandidat,
        target_kalori
    )

    return (
        bmr,
        tdee,
        target_kalori,
        paket
    )

# =====================
# STREAMLIT
# =====================

st.set_page_config(
    page_title="Sistem Rekomendasi Menu Makanan",
    layout="wide"
)

st.title(
    "🍽️ Sistem Rekomendasi Menu Makanan Harian"
)

st.write(
    f"Jumlah menu dalam dataset: {len(makanan)}"
)

col1, col2 = st.columns(2)

with col1:

    usia = st.number_input(
        "Usia",
        min_value=15,
        max_value=80,
        value=22
    )

    jk = st.selectbox(
        "Jenis Kelamin",
        [
            "L",
            "P"
        ]
    )

with col2:

    bb = st.number_input(
        "Berat Badan (kg)",
        min_value=30,
        max_value=200,
        value=65
    )

    tb = st.number_input(
        "Tinggi Badan (cm)",
        min_value=120,
        max_value=220,
        value=170
    )

aktivitas = st.selectbox(
    "Aktivitas Harian",
    [
        "Ringan",
        "Sedang",
        "Berat"
    ]
)

if st.button(
    "Rekomendasikan Menu"
):

    bmr, tdee, target, paket = rekomendasi(

        usia=usia,

        jenis_kelamin=jk,

        berat_badan=bb,

        tinggi_badan=tb,

        aktivitas=aktivitas

    )

    st.success(
        f"BMR : {bmr:.2f} kkal"
    )

    st.success(
        f"TDEE : {tdee:.2f} kkal"
    )

    st.success(
        f"Target Kalori per Makan : {target:.2f} kkal"
    )

    st.subheader(
        "Top 5 Rekomendasi Paket Menu"
    )

    st.dataframe(
        paket,
        use_container_width=True
    )