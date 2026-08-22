"""Test V-5 — profils des 10 voix (dont enfants), voix personnalisées/fine-tunées, prep fine-tuning."""


def test_profiles_cover_ten_voices():
    from ai_engine.modules.voice.profiles import all_profiles
    profs = all_profiles()
    assert len(profs) == 10
    children = [p for p in profs if p["is_child"]]
    assert len(children) == 4  # 2 garçons + 2 filles
    # les voix enfants sont plus aiguës et plus vives qu'une voix médium adulte
    for c in children:
        assert c["pitch_semitones"] > 0 and c["length_scale"] < 1.0


def test_base_gender_mapping():
    from ai_engine.modules.voice.profiles import base_gender
    assert base_gender("lz-m2-warm") == "male"
    assert base_gender("lz-b1-playful") == "male"   # garçon -> base masculine
    assert base_gender("lz-g1-cheerful") == "female"  # fille -> base féminine


def test_custom_voice_register_and_resolve(tmp_path):
    from ai_engine.modules.voice.profiles import get_custom_voice_store
    store = get_custom_voice_store()
    # modèle absent -> enregistré mais non résolu
    rec = store.register("lz-f2-warm", "ln", str(tmp_path / "ln.onnx"), quality="alpha")
    assert rec["exists"] is False
    assert store.resolve("lz-f2-warm", "ln") is None
    # crée le fichier -> devient résolu (utilisable)
    (tmp_path / "ln.onnx").write_bytes(b"fake-onnx")
    assert store.resolve("lz-f2-warm", "ln") == str(tmp_path / "ln.onnx")
    assert any(r["lang"] == "ln" for r in store.list("ln"))


def test_custom_voice_unknown_voice_rejected(tmp_path):
    from ai_engine.modules.voice.profiles import get_custom_voice_store
    try:
        get_custom_voice_store().register("pas-une-voix", "sw", str(tmp_path / "x.onnx"))
        assert False
    except ValueError:
        pass


def test_finetune_prepare_writes_manifest():
    from ai_engine.modules.voice.finetune import list_datasets, prepare_dataset
    pairs = [
        {"audio": "a1.wav", "text": "Mbote na yo"},
        {"audio": "a2.wav", "text": "Mbote na yo"},   # doublon texte -> écarté
        {"audio": "", "text": "sans audio"},           # écarté
        {"audio": "a3.wav", "text": "Boni ozali"},
    ]
    meta = prepare_dataset(pairs, lang="ln", voice_id="lz-f2-warm", task="tts")
    assert meta["pairs_kept"] == 2 and meta["dropped"] == 2
    assert any(d["lang"] == "ln" for d in list_datasets())


def test_finetune_bad_task_rejected():
    from ai_engine.modules.voice.finetune import prepare_dataset
    try:
        prepare_dataset([{"audio": "a.wav", "text": "x"}], lang="sw", voice_id="lz-m1-bright", task="bogus")
        assert False
    except ValueError:
        pass


def test_endpoints(client):
    profs = client.get("/v1/voice/profiles").json()
    assert len(profs) == 10
    r = client.get("/v1/voice/profiles/lz-b1-playful").json()
    assert r["is_child"] is True
    assert client.get("/v1/voice/profiles/nope").status_code == 404
    # enregistrer une voix fine-tunée ln
    r = client.post("/v1/voice/voices/lz-f2-warm/model",
                    json={"lang": "ln", "model_path": "/tmp/ln-voice.onnx"})
    assert r.status_code == 200 and r.json()["lang"] == "ln"
    # prep fine-tuning
    r = client.post("/v1/voice/finetune/prepare",
                    json={"pairs": [{"audio": "a.wav", "text": "Mbote"}], "lang": "ln", "voice_id": "lz-f2-warm"})
    assert r.status_code == 200 and r.json()["pairs_kept"] == 1
