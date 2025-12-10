import json
import secrets
import os
from datetime import datetime

# Nama file database key
DB_FILE = "database_key.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"keys": {}}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"keys": {}}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generate_new_key():
    # Membuat 9 karakter acak (Huruf Besar + Angka)
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    key = "".join(secrets.choice(alphabet) for i in range(9))
    
    db = load_db()
    
    # Simpan status "active"
    db["keys"][key] = {
        "status": "active",
        "created_at": str(datetime.now())
    }
    
    save_db(db)
    print("\n" + "="*40)
    print(f"✅ KEY BERHASIL DIBUAT: {key}")
    print("="*40)
    print("Status: ACTIVE (Siap diberikan ke pembeli)")
    print("Key ini akan hangus otomatis setelah dipakai login.\n")

if __name__ == "__main__":
    print("=== ADMIN PANEL KEY GENERATOR ===")
    while True:
        print("1. Buat Key Baru")
        print("2. Cek List Key")
        print("3. Reset Semua Key (Hapus Data)")
        print("4. Keluar")
        pilih = input("Pilih menu (1-4): ")
        
        if pilih == "1":
            generate_new_key()
        elif pilih == "2":
            db = load_db()
            print(json.dumps(db, indent=4))
        elif pilih == "3":
            if input("Yakin hapus semua key? (y/n): ").lower() == 'y':
                save_db({"keys": {}})
                print("Database di-reset.")
        elif pilih == "4":
            break
        else:
            print("Pilihan salah!")