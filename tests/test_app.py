"""
Tests for backend/app.py (Flask API)

Run with:  pytest tests/ -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import json
import io
import pytest
from unittest.mock import MagicMock, patch

sys.stdout = sys.__stdout__

@pytest.fixture(scope="session")
def app():
    fake_tokenizer   = MagicMock()
    fake_transcriber = MagicMock()
    fake_morphology  = MagicMock()
    fake_phonology   = MagicMock()
    fake_generator   = MagicMock()

    fake_transcriber.transcribe_text.return_value = [
        {"original": "𐀷𐀙𐀏", "transliteration": "wa-na-ka", "token_count": 3}
    ]
    fake_transcriber.get_phonetic_form.return_value = "wanaka"

    morph = MagicMock()
    morph.to_dict.return_value = {
        "stem": "wanak", "ending": "a", "pos": "noun",
        "case": "nominative", "number": "singular", "confidence": 0.9,
    }
    fake_morphology.segment_word.return_value = [morph]
    fake_morphology.lexicon = {
        "wa-na-ka": {
            "meaning": "king",
            "classical_greek": "anax",
            "reconstruction": "wanaks",
            "pos": "noun",
            "declension": "a_stem",
            "stem": "wanak",
            "pie_root": "*h2neg-",
            "pie_meaning": "to reach",
            "cognates": {"latin": "nancisci"},
        }
    }
    fake_morphology.ending_map = {}

    fake_path = MagicMock()
    fake_path.mycenaean = "wanaks"
    fake_path.classical = "anax"
    fake_path.changes_applied = []
    fake_path.to_dict.return_value = {"stages": [
        {"form": "wanaks", "period": "Mycenaean"},
        {"form": "anax",   "period": "Classical"},
    ]}
    fake_phonology.apply_changes.return_value = fake_path
    fake_phonology.explain_divergence.return_value = ["Digamma loss: w -> 0"]
    fake_phonology.rules = []

    fake_form = MagicMock()
    fake_form.to_dict.return_value = {
        "form": "wanaka", "case": "nominative",
        "number": "singular", "attested": True,
    }
    fake_generator.generate_all_forms.return_value = {"nom_sg": [fake_form]}

    patches = [
        patch("core.tokenizer.LinearBTokenizer",       return_value=fake_tokenizer),
        patch("core.transcriber.LinearBTranscriber",   return_value=fake_transcriber),
        patch("core.morphology.MorphologicalAnalyzer", return_value=fake_morphology),
        patch("core.phonology.PhonologyEngine",        return_value=fake_phonology),
        patch("core.generator.ParadigmGenerator",      return_value=fake_generator),
    ]
    for p in patches:
        p.start()

    from app import app as flask_app
    flask_app.config["TESTING"] = True
    yield flask_app

    for p in patches:
        p.stop()


@pytest.fixture
def client(app):
    return app.test_client()


class TestIndex:
    def test_returns_200(self, client):
        assert client.get("/").status_code == 200


class TestHealth:
    def test_operational(self, client):
        data = json.loads(client.get("/health").data)
        assert data["status"] == "operational"

    def test_all_engines_reported(self, client):
        data = json.loads(client.get("/health").data)
        for key in ("tokenizer", "transcriber", "morphology", "phonology", "generator"):
            assert key in data["engines"]


class TestTranscribe:
    def test_200_with_text(self, client):
        assert client.post("/api/transcribe", json={"text": "𐀷𐀙𐀏"}).status_code == 200

    def test_response_has_words(self, client):
        r = client.post("/api/transcribe", json={"text": "𐀷𐀙𐀏"})
        assert "words" in json.loads(r.data)

    def test_word_has_required_fields(self, client):
        r = client.post("/api/transcribe", json={"text": "𐀷𐀙𐀏"})
        word = json.loads(r.data)["words"][0]
        for key in ("original", "transliteration", "phonetic"):
            assert key in word

    def test_empty_text_400(self, client):
        assert client.post("/api/transcribe", json={"text": ""}).status_code == 400

    def test_missing_key_400(self, client):
        assert client.post("/api/transcribe", json={}).status_code == 400


class TestAnalyze:
    def test_200_with_word(self, client):
        assert client.post("/api/analyze", json={"word": "wa-na-ka"}).status_code == 200

    def test_has_analyses(self, client):
        r = client.post("/api/analyze", json={"word": "wa-na-ka"})
        assert "analyses" in json.loads(r.data)

    def test_empty_word_400(self, client):
        assert client.post("/api/analyze", json={"word": ""}).status_code == 400


class TestDiachronic:
    def test_200_with_both_forms(self, client):
        r = client.post("/api/diachronic",
                        json={"mycenaean": "wanaks", "classical": "anax"})
        assert r.status_code == 200

    def test_has_stages(self, client):
        r = client.post("/api/diachronic",
                        json={"mycenaean": "wanaks", "classical": "anax"})
        assert "stages" in json.loads(r.data)

    def test_missing_classical_400(self, client):
        assert client.post("/api/diachronic",
                           json={"mycenaean": "wanaks"}).status_code == 400

    def test_missing_mycenaean_400(self, client):
        assert client.post("/api/diachronic",
                           json={"classical": "anax"}).status_code == 400


class TestGenerate:
    def test_200_with_stem(self, client):
        assert client.post("/api/generate", json={"stem": "wanak"}).status_code == 200

    def test_has_forms_and_total(self, client):
        r = client.post("/api/generate", json={"stem": "wanak"})
        data = json.loads(r.data)
        assert "forms" in data and "total" in data

    def test_no_stem_400(self, client):
        assert client.post("/api/generate", json={}).status_code == 400

    def test_coverage_is_percentage(self, client):
        r = client.post("/api/generate", json={"stem": "wanak"})
        assert "%" in json.loads(r.data)["coverage"]


class TestGenerateFromLexicon:
    def test_known_word_200(self, client):
        assert client.get("/api/generate/wa-na-ka").status_code == 200

    def test_unknown_word_404(self, client):
        assert client.get("/api/generate/not-real").status_code == 404

    def test_has_lemma_data(self, client):
        r = client.get("/api/generate/wa-na-ka")
        data = json.loads(r.data)
        assert "lemma_data" in data
        assert data["lemma_data"]["meaning"] == "king"


class TestLexicon:
    def test_200(self, client):
        assert client.get("/api/lexicon").status_code == 200

    def test_has_words_list(self, client):
        data = json.loads(client.get("/api/lexicon").data)
        assert "words" in data and isinstance(data["words"], list)

    def test_each_word_has_fields(self, client):
        for word in json.loads(client.get("/api/lexicon").data)["words"]:
            assert "transliteration" in word
            assert "meaning" in word