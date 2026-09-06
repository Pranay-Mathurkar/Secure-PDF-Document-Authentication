"""
End-to-end verification test script.
Tests:
1. Original PDF creation.
2. Securing PDF via API.
3. Verifying authentic secured PDF.
4. Tampering Page 1 and verifying detection as MODIFIED.
5. Verifying single-page PDF as INVALID.
"""
import requests
import fitz

API_BASE = "http://127.0.0.1:8000/api/v1"

def create_sample_pdf(filepath: str, text: str):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text(fitz.Point(72, 100), "UNIVERSITY ACADEMIC TRANSCRIPT", fontsize=18)
    page.insert_text(fitz.Point(72, 140), f"Student Record: {text}", fontsize=12)
    page.insert_text(fitz.Point(72, 170), "Grade: A+", fontsize=12)
    doc.save(filepath)
    doc.close()

# 1. Create sample original PDF
orig_path = "sample_transcript.pdf"
create_sample_pdf(orig_path, "Alice Smith (ID: 2026-CS-101)")
print("1. Created original PDF:", orig_path)

# 2. Secure it via API
with open(orig_path, "rb") as f:
    resp = requests.post(f"{API_BASE}/generate/secure-pdf", files={"file": (orig_path, f, "application/pdf")})
assert resp.status_code == 200, f"Securing failed: {resp.text}"
gen_data = resp.json()
print("2. Secured PDF created:")
print("   - Filename:", gen_data["file_name"])
print("   - SHA-256:", gen_data["sha256_hash"])
print("   - Download URL:", gen_data["download_url"])

# Download the secured PDF
download_resp = requests.get(f"http://127.0.0.1:8000{gen_data['download_url']}")
assert download_resp.status_code == 200
secured_path = "secured_transcript.pdf"
with open(secured_path, "wb") as f:
    f.write(download_resp.content)
print("   - Downloaded secured PDF, size:", len(download_resp.content), "bytes")

# 3. Verify the Authentic secured PDF
with open(secured_path, "rb") as f:
    verify_resp = requests.post(f"{API_BASE}/verify/verify-pdf", files={"file": (secured_path, f, "application/pdf")})
assert verify_resp.status_code == 200
ver_data = verify_resp.json()
print("3. Verification of Secured PDF:")
print("   - Authentic:", ver_data["is_authentic"])
print("   - Status Text:", ver_data["status_text"])
print("   - Original Hash:", ver_data["original_hash"])
print("   - Calculated Hash:", ver_data["calculated_hash"])
assert ver_data["is_authentic"] == True
assert ver_data["status_text"] == "AUTHENTIC"

# 4. Tamper with Page 1 and test verification
doc = fitz.open(secured_path)
page_1 = doc[0]
# Tamper text: draw an altered grade over it
page_1.draw_rect(fitz.Rect(70, 160, 200, 185), color=(1, 1, 1), fill=(1, 1, 1))
page_1.insert_text(fitz.Point(72, 170), "Grade: F (TAMPERED)", fontsize=12, color=(1, 0, 0))
tampered_path = "tampered_transcript.pdf"
doc.save(tampered_path)
doc.close()
print("4. Created tampered PDF:", tampered_path)

with open(tampered_path, "rb") as f:
    tamper_resp = requests.post(f"{API_BASE}/verify/verify-pdf", files={"file": (tampered_path, f, "application/pdf")})
assert tamper_resp.status_code == 200
tamper_data = tamper_resp.json()
print("   - Verification of Tampered PDF:")
print("   - Authentic:", tamper_data["is_authentic"])
print("   - Status Text:", tamper_data["status_text"])
print("   - Original Hash:", tamper_data["original_hash"])
print("   - Calculated Hash:", tamper_data["calculated_hash"])
assert tamper_data["is_authentic"] == False
assert tamper_data["status_text"] == "MODIFIED"

# 5. Test invalid single-page PDF
with open(orig_path, "rb") as f:
    invalid_resp = requests.post(f"{API_BASE}/verify/verify-pdf", files={"file": (orig_path, f, "application/pdf")})
invalid_data = invalid_resp.json()
print("5. Verification of 1-Page PDF (Invalid):")
print("   - Status Text:", invalid_data["status_text"])
assert invalid_data["status_text"] == "INVALID"

print("\nALL FORENSIC VERIFICATION TESTS PASSED SUCCESSFULLY! 100% OPERATIONAL.")
