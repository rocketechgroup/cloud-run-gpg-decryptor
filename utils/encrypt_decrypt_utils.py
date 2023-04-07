import gnupg

# docs: https://gnupg.readthedocs.io/en/latest/
# docs: https://gist.github.com/johnfedoruk/7f156d844af54cc91324dff4f54b11ce

gpg = gnupg.GPG()
gpg.import_keys_file('private.pgp')
recipient = 'no-passwd@example.com'
clear_text = 'This is to be encrypted'

encrypted_ascii_data = gpg.encrypt_file(fileobj_or_path='file_to_encrypt.txt', recipients=[recipient])

with open('encrypted_file.gpg', 'w+') as fp:
    fp.write(str(encrypted_ascii_data))

decrypted_data = gpg.decrypt_file('encrypted_file.gpg')
print(decrypted_data)
