import streamlit as st
import pickle
import pandas as pd
import os
import requests
import re
from urllib.parse import quote


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="CINEMOC - Movie Recommendation System",
    page_icon="🎬",
    layout="wide"
)


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_resource
def load_data():

    with open("movie_list.pkl", "rb") as file:
        movies = pickle.load(file)

    with open("similarity.pkl", "rb") as file:
        similarity = pickle.load(file)

    movies["movie_id"] = pd.to_numeric(
        movies["movie_id"],
        errors="coerce"
    )

    return movies, similarity


movies, similarity = load_data()


# =========================================================
# POSTER SETTINGS
# =========================================================

POSTER_FOLDER = "posters"

os.makedirs(POSTER_FOLDER, exist_ok=True)


session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    )
})


# =========================================================
# FIND AND DOWNLOAD POSTER
# =========================================================

def find_and_download_poster(movie_id, title):

    if pd.isna(movie_id):
        return None

    movie_id = int(movie_id)

    poster_path = os.path.join(
        POSTER_FOLDER,
        f"{movie_id}.jpg"
    )

    # If poster already exists locally
    if os.path.exists(poster_path):

        if os.path.getsize(poster_path) > 1000:
            return poster_path

    try:

        search_url = (
            "https://www.themoviedb.org/search/movie?query="
            + quote(str(title))
        )

        response = session.get(
            search_url,
            timeout=10
        )

        if response.status_code != 200:
            return None

        html = response.text

        # Find media.themoviedb.org poster URLs
        matches = re.findall(
            r'https://media\.themoviedb\.org/t/p/[^"\']+?\.jpg',
            html
        )

        if not matches:
            return None

        poster_url = None

        for url in matches:

            url = url.replace("&amp;", "&")

            if url not in matches:
                continue

            poster_url = url
            break

        if not poster_url:
            return None

        # Change image size to high-quality poster
        poster_url = re.sub(
            r'/t/p/[^/]+/',
            '/t/p/w600_and_h900_face/',
            poster_url
        )

        image_response = session.get(
            poster_url,
            timeout=10
        )

        if image_response.status_code != 200:
            return None

        content_type = image_response.headers.get(
            "Content-Type",
            ""
        ).lower()

        if "image" not in content_type:
            return None

        if len(image_response.content) < 1000:
            return None

        with open(
            poster_path,
            "wb"
        ) as file:

            file.write(
                image_response.content
            )

        return poster_path

    except Exception:
        return None


# =========================================================
# DISPLAY POSTER
# =========================================================

def display_poster(movie_id, title):

    poster_path = find_and_download_poster(
        movie_id,
        title
    )

    if poster_path and os.path.exists(poster_path):

        st.image(
            poster_path,
            use_container_width=True
        )

    else:

        st.markdown(
            """
            <div style="
                height:350px;
                display:flex;
                align-items:center;
                justify-content:center;
                background:#151515;
                border-radius:12px;
                border:1px solid #333;
                color:#777;
                font-size:14px;
            ">
                Poster not available
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# RECOMMENDATION FUNCTION
# =========================================================

def recommend(movie):

    movie_index = movies[
        movies["title"] == movie
    ].index[0]

    distances = similarity[movie_index]

    movie_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )

    recommendations = []

    for i in movie_list[1:6]:

        index = i[0]

        title = movies.iloc[index]["title"]

        movie_id = movies.iloc[index]["movie_id"]

        score = float(i[1])

        recommendations.append(
            (
                title,
                movie_id,
                score
            )
        )

    return recommendations


# =========================================================
# CINEMOC DESIGN
# =========================================================

st.markdown(
    """
    <style>

    /* MAIN BACKGROUND */

    .stApp {
        background:
        radial-gradient(
            circle at top,
            #1b1b1b 0%,
            #080808 45%,
            #000000 100%
        );

        color:white;
    }


    /* REMOVE TOP SPACE */

    .block-container {
        padding-top:2rem;
        padding-bottom:2rem;
    }


    /* CINEMOC TITLE */

    .cinemoc-title {

        text-align:center;

        font-size:58px;

        font-weight:900;

        letter-spacing:8px;

        color:#ffffff;

        margin-top:10px;

        margin-bottom:5px;

        text-shadow:
            0 0 10px rgba(255,255,255,0.15),
            0 0 30px rgba(255,0,0,0.15);
    }


    /* TAGLINE */

    .cinemoc-tagline {

        text-align:center;

        color:#999999;

        font-size:15px;

        letter-spacing:3px;

        margin-bottom:40px;
    }


    /* SEARCH BOX */

    div[data-baseweb="input"] {

        background:#111111 !important;

        border:1px solid #333333 !important;

        border-radius:10px !important;
    }


    div[data-baseweb="input"] input {

        color:white !important;

        font-size:16px !important;
    }


    /* SELECT BOX */

    div[data-baseweb="select"] > div {

        background:#111111 !important;

        border:1px solid #333333 !important;

        color:white !important;

        border-radius:10px !important;
    }


    /* BUTTON */

    .stButton > button {

        width:100%;

        background:#ffffff;

        color:#000000;

        border:none;

        border-radius:10px;

        padding:12px;

        font-size:16px;

        font-weight:700;

        transition:0.2s;
    }


    .stButton > button:hover {

        background:#dddddd;

        color:#000000;

        transform:scale(1.01);
    }


    /* MOVIE TITLE */

    .movie-title {

        text-align:center;

        color:#ffffff;

        font-size:17px;

        font-weight:700;

        margin-top:12px;

        min-height:45px;

        display:flex;

        align-items:center;

        justify-content:center;
    }


    /* FOOTER */

    .footer {

        text-align:center;

        color:#555555;

        margin-top:50px;

        font-size:13px;

        letter-spacing:1px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="cinemoc-title">CINEMOC</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="cinemoc-tagline">DISCOVER YOUR NEXT MOVIE</div>',
    unsafe_allow_html=True
)


# =========================================================
# SEARCH
# =========================================================

search = st.text_input(
    "Search movie",
    placeholder="Type a movie name..."
)


# =========================================================
# MOVIE SELECTION
# =========================================================

movie_options = movies["title"].tolist()

selected_movie = None


if search.strip():

    search_lower = search.strip().lower()

    matching_movies = [
        movie
        for movie in movie_options
        if search_lower in movie.lower()
    ]

    if matching_movies:

        selected_movie = st.selectbox(
            "Select movie",
            matching_movies
        )

    else:

        st.warning(
            "No movie found in the dataset."
        )


# =========================================================
# RECOMMEND BUTTON
# =========================================================

if selected_movie:

    if st.button("🎬 Recommend Movies"):

        recommendations = recommend(
            selected_movie
        )

        st.markdown(
            "<br>",
            unsafe_allow_html=True
        )

        cols = st.columns(5)

        for col, recommendation in zip(
            cols,
            recommendations
        ):

            title = recommendation[0]

            movie_id = recommendation[1]

            similarity_score = recommendation[2]

            with col:

                # Poster
                display_poster(
                    movie_id,
                    title
                )

                # Movie title
                st.markdown(
                    f"""
                    <div class="movie-title">
                        {title}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # ONLY SIMILARITY PERCENTAGE
                st.markdown(
                    f"""
                    <div style="
                        text-align:center;
                        margin-top:5px;
                        margin-bottom:5px;
                        font-size:14px;
                        color:#FFFFFF;
                        font-weight:bold;
                    ">
                        {similarity_score:.2%}
                    </div>
                    """,
                    unsafe_allow_html=True
                )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
        CINEMOC • MOVIE RECOMMENDATION SYSTEM
    </div>
    """,
    unsafe_allow_html=True
)