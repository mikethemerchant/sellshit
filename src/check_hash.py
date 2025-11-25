import hashlib

def _hash_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

msg = "You have my size?"
print(f"Message: '{msg}'")
print(f"Hash: {_hash_text(msg)}")

# Check against known hashes
known = {
    "Alex": "2802ede77dfc11d48be2a732868704a5ef8b37ebecb33f4102f84c8a7b789458",
    "WiFi": "bb47b8ff5f623996f8f46b80933095a90e29a5bb4442ac09498c9e9e8fc1cbf4",
    "Pisit": "e3a57785b91fea3da8810e83e288077e834a9e2930fbfce704ffb636b0ab8962",
    "Chris": "e4ff8025e1cb0b1d107869a38d5b984dea092a45e99f7870d65d0f7833b0d138",
    "Patch": "ca03b6f741aa14b50fd08dba924059f18ee7fc0cc5aedbfad1bb5d1628ab65db"
}

for name, h in known.items():
    if h == _hash_text(msg):
        print(f"MATCH! {name} has this message.")
