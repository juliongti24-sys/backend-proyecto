from passlib.context import CryptContext
import sys

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_hash():
    password = "a" * 50
    try:
        h = pwd_context.hash(password)
        print(f"Hash successful for 50 chars: {h[:20]}...")
        
        # Test 73 chars (should fail or work depending on passlib version)
        long_password = "a" * 73
        try:
            h2 = pwd_context.hash(long_password)
            print(f"Hash successful for 73 chars: {h2[:20]}...")
        except Exception as e:
            print(f"Hash FAILED for 73 chars as expected (or error): {type(e).__name__}: {e}")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_hash()
