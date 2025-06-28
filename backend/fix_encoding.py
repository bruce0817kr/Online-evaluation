import re

with open('server.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Replace all Korean text with English equivalents
replacements = {
    '추': '',
    '용이처리 류': 'User processing error',
    '중복 메는 화번호 체크': 'Check for duplicate email or phone number',
    ' 청역는지 체크': 'Check if secretary request already exists',
    ' 청역습다. 관리자 인기다주요.': 'Secretary request already exists. Please wait for admin approval.',
    '청 역 ': 'Create secretary approval request',
    '간사 원가청료었니 관리자 인 로그이 가합다.': 'Secretary request submitted successfully. Please wait for admin approval.',
    '관리자근 가합다': 'Admin access required',
    '청 역 찾기': 'Find secretary request',
    '청 역찾을 습다': 'Secretary request not found',
    '용계정 성': 'Create user account',
    '름로그ID용': 'Use name as login ID',
    '화번호비번호용': 'Use phone number as password',
    '용성': 'Create user account',
    '청 태 데트': 'Update request status',
    '간사 계정성었니': 'Secretary account created successfully',
    '간사 청거었니': 'Secretary request rejected',
    ' 존재는 이입다': 'User already exists',
    '검증용로 출경우 간단보반환': 'For validation purposes, return simple information',
    '증용인 경우 권한 인': 'For authenticated users, verify permissions',
    'MongoDB 이 전게 UserResponse변': 'Convert MongoDB documents to UserResponse objects',
    'User.from_mongo용여 User 객체 성 (_id id 변함)': 'Use User.from_mongo to create User object (converts _id to id)',
    ' 존재는 원니(름/화번호 중복)': 'User already exists (name/phone number duplicate)'
}

for korean, english in replacements.items():
    content = content.replace(korean, english)

# Remove any remaining non-ASCII characters in comments and strings
content = re.sub(r'[^\x00-\x7F]+', '', content)

# Fix common syntax issues
content = re.sub(r'detail="Request already processed"(?!\))', 'detail="Request already processed")', content)

with open('server_fixed.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed encoding issues and saved to server_fixed.py')
