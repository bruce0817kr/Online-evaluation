#!/usr/bin/env python3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

password = "evaluator123"
hash_value = pwd_context.hash(password)

print(f"Password: {password}")
print(f"Hash: {hash_value}")

# Test verification
is_valid = pwd_context.verify(password, hash_value)
print(f"Verification: {is_valid}")