import random
import string

def generate_key():
    # Format: XXXX-XXXX-XXXX-XXXX
    chars = string.ascii_uppercase + string.digits
    # Remove O, 0, I, 1 to avoid confusion
    chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
    
    parts = []
    for _ in range(4):
        parts.append(''.join(random.choices(chars, k=4)))
    
    return "-".join(parts)

if __name__ == "__main__":
    print("\n--- OrbitSwipe License Key Generator ---")
    num = int(input("How many keys do you want to generate? "))
    keys = [generate_key() for _ in range(num)]
    
    print("\nGenerated Keys:")
    print("----------------")
    for k in keys:
        print(k)
    
    print("\nCopy these keys and add them to your VALID_KEYS environment variable in Vercel.")
    print("Format: [\"KEY1\", \"KEY2\", ...]\n")
