import streamlit as st # type: ignore
import pandas as pd # type: ignore

from sklearn.preprocessing import MinMaxScaler # type: ignore
from sklearn.metrics.pairwise import cosine_similarity # type: ignore

from itertools import combinations

# =====================
# LOAD DATA
# =====================

try:
    makanan = pd.read_excel(
        "data_makanan.xlsx",
        sheet_name="Menu"
    )
except Exception as e:
    st.error(f"Gagal membaca file Excel: {e}")
    st.stop()

# Pastikan dataset memiliki 5 kolom
if len(makanan.columns) != 5:
    st.error(
        "Dataset harus memiliki 5 kolom: nama_menu, kalori, protein, lemak, karbohidrat"
    )
    st.stop()

makanan.columns = [
    'nama_menu',
    'kalori',
    'protein',
    'lemak',
    'karbohidrat'
]

# =====================
# BMR
# =====================

def hitung_bmr(
    usia,
    jenis_kelamin,
    berat_badan,
    tinggi_badan,
):

    if jenis_kelamin == "L":

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
            (10 * berat_badan)
            +
            (6.25 * tinggi_badan)
            -
            (5 * usia)
            -
            161
        )

# =====================
# FAKTOR AKTIVITAS
# =====================

faktor = {

    "Ringan": 1.375,

    "Sedang": 1.55,

    "Berat": 1.725

}

# =====================
# KANDIDAT MENU
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

    target_karbo = (
        target_kalori * 0.60
    ) / 4

    fitur = [

        'protein',

        'lemak',

        'karbohidrat'

    ]

    scaler = MinMaxScaler()

    makanan_scaled = scaler.fit_transform(
        makanan[fitur]
    )

    profil_user = [[

        target_protein,

        target_lemak,

        target_karbo

    ]]

    profil_scaled = scaler.transform(
        profil_user
    )

    similarity = cosine_similarity(
        profil_scaled,
        makanan_scaled
    )

    data = makanan.copy()

    data['Similarity'] = similarity.flatten()

    return data.sort_values(
        by='Similarity',
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
            'kalori'
        ].sum()

        rata_similarity = paket[
            'Similarity'
        ].mean()

        selisih = abs(
            target_kalori
            -
            total_kalori
        )

        hasil.append({

            'Menu 1':
            paket.iloc[0]['nama_menu'],

            'Menu 2':
            paket.iloc[1]['nama_menu'],

            'Menu 3':
            paket.iloc[2]['nama_menu'],

            'Total Kalori':
            total_kalori,

            'Similarity':
            round(
                rata_similarity,
                4
            ),

            'Selisih':
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
            'Selisih',
            'Similarity'
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
        faktor[
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
        tdee,
        target_kalori,
        paket
    )

# =====================
# STREAMLIT
# =====================

st.set_page_config(
    page_title="Sistem Rekomendasi Menu",
    layout="wide"
)

st.title(
    "🍽️ Sistem Rekomendasi Menu Makanan Harian"
)

st.write(
    "Masukkan data diri untuk mendapatkan rekomendasi menu berdasarkan kebutuhan kalori."
)

usia = st.number_input(
    "Usia",
    min_value=15,
    max_value=80,
    value=25
)

jk = st.selectbox(
    "Jenis Kelamin",
    ["L", "P"]
)

bb = st.number_input(
    "Berat Badan (kg)",
    min_value=30,
    max_value=150,
    value=60
)

tb = st.number_input(
    "Tinggi Badan (cm)",
    min_value=120,
    max_value=220,
    value=170
)

aktivitas = st.selectbox(
    "Aktivitas",
    [
        "Ringan",
        "Sedang",
        "Berat"
    ]
)

if st.button(
    "Rekomendasikan Menu"
):

    tdee, target, paket = rekomendasi(
        usia=usia,
        jenis_kelamin=jk,
        berat_badan=bb,
        tinggi_badan=tb,
        aktivitas=aktivitas
    )

    st.success(
        f"TDEE : {tdee:.2f} kkal/hari"
    )

    st.success(
        f"Target Kalori per Makan : {target:.2f} kkal"
    )

    st.subheader(
        "Top 5 Paket Menu"
    )

    st.dataframe(
        paket,
        use_container_width=True
    )