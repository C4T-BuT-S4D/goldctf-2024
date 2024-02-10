# Gold CTF 2024 | digger

Service `digger` is an Encryption-as-a-Service application.

Source code is available here: [/internal/digger/](/internal/digger/).

## Overview

Service is given as a compiled, dynamically linked binary file.

```bash
$ file ./digger    
./digger: ELF 64-bit LSB pie executable, x86-64, version 1 (GNU/Linux), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1]=481e676232d8f549acbad52e090127912e1d098a, for GNU/Linux 3.2.0, not stripped
```

```bash
$ ldd ./digger   
	linux-vdso.so.1 (0x00007ffd71fec000)
	libstdc++.so.6 => /lib/x86_64-linux-gnu/libstdc++.so.6 (0x00007fe5617af000)
	libgcc_s.so.1 => /lib/x86_64-linux-gnu/libgcc_s.so.1 (0x00007fe56178f000)
	libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007fe561567000)
	libm.so.6 => /lib/x86_64-linux-gnu/libm.so.6 (0x00007fe561480000)
	/lib64/ld-linux-x86-64.so.2 (0x00007fe561a13000)
```

```bash
$ checksec ./digger
    Arch:     amd64-64-little
    RELRO:    Full RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      PIE enabled
```

It's a console application with text-based interface.

```bash
$ ./digger
=====================
=   Digger v0.0.1   =
=====================

> HELP
use REGISTER, LOGIN, LOGOUT, ENCRYPT, DECRYPT or EXIT
> 
```

Each user is identified as unique username, authenticated with password and stores the secret data.

```
> REGISTER
username: hacker1337
password: abcdabcd
secret: flagflagflagflag
successfully registered
> LOGIN
username: hacker1337
password: abcdabcd
successfully logged in, your secret: flagflagflagflag
> LOGOUT
successfully logged out
> 
```

Service can encrypt and decrypt any data for authorized users.

```
> LOGIN
username: hacker1337
password: abcdabcd
successfully logged in, your secret: flagflagflagflag
> ENCRYPT
plaintext (hex): AAAABBBBCCCCDDDDAAAABBBBCCCCDDDD
ciphertext (hex):
1550e67e14078c091550e67e14078c09
> DECRYPT
ciphertext (hex): 1550e67e14078c091550e67e14078c09
plaintext (hex):
aaaabbbbccccddddaaaabbbbccccdddd
> 
```

But for anonymous users only encryption is available.

```
> ENCRYPT
username: hacker1337
plaintext (hex): AAAABBBBCCCCDDDDAAAABBBBCCCCDDDD
ciphertext (hex):
1550e67e14078c091550e67e14078c09
> DECRYPT
you need to login first
> 
```

Flag is stored in user's secret, username is given as public flag id (attack data).

## Analysis

The binary is written in C++, not stripped, compiled without optimizations (`-O0`), and densily decomposed by functions, so reverse engineering should be possible in short time.

I won't cover the entire analysis process, just notice the milestones.

### Authentication

The service uses filesystem as a storage:

- password in `./storage/passwords/<username>` file
- secret in `./storage/secrets/<username>` file

Also there is an in-memory-cache for users' structs in order to reduce count of system calls.

The user's password is never printed to the output, so there is no way to leak it directly.

### Encryption

The cipher is [DES](https://en.wikipedia.org/wiki/Data_Encryption_Standard) in [ECB](https://en.wikipedia.org/wiki/Block_cipher_mode_of_operation#Electronic_codebook_(ECB)) mode. The user's password is used as a key.

Before encryption (and decryption) process a DES object is created. The input is splitted by 64-bit blocks, each block is encrypted independently, and then ciphertext is returned as joined encrypted blocks.

The DES cipher also uses a specially constructed object called Context, which contains all constant values and tables used in cipher ([DES supplementary material](https://en.wikipedia.org/wiki/DES_supplementary_material)).

The contexts are stored in in-memory-cache too in order to reuse constructed objects, the caching key is username.

### Conclusion

Attack target is the authorization system, it's the only place where the flag is printed. But it's completely secure at the first sight, because passwords are correctly compared, the input is sanitized.

But there is another way to leak the password. Since it's used as a DES key, the anonymous user could break the cipher itself and extract the encryption key.

## Vulnerability

I will explicitly describe some important assumptions.

### Reconstruction of context structure

Let's look how the context is constructed.

```c
// Digger::Server::Backend::Encrypt
Digger::Crypto::Context::Context(
    (unsigned int)ctx,
    (unsigned int)&Digger::Crypto::Tables::PC1,
    (unsigned int)&Digger::Crypto::Tables::PC2,
    (unsigned int)&Digger::Crypto::Tables::KEY_ROTATION,
    (unsigned int)&Digger::Crypto::Tables::INITIAL_PERMUTATION,
    (unsigned int)&Digger::Crypto::Tables::ROUND_PERMUTATION,
    (__int64)&Digger::Crypto::Tables::FINAL_PERMUTATION,
    (__int64)&Digger::Crypto::Tables::EXPANSION,
    (__int64)&Digger::Crypto::Tables::SBOX);
```

All tables are hardcoded in binary's data, except for SBOX table which is constructed during the static initialization.

```c
// __static_initialization_and_destruction_0(int a1, int a2)
qmemcpy(v4, &SBOX, 0x1000uLL);
std::allocator<std::array<unsigned long,64ul>>::allocator(&v3, (char *)&SBOX + 4096, &SBOX);
std::vector<std::array<unsigned long,64ul>>::vector(&Digger::Crypto::Tables::SBOX, v4, 8LL, &v3);
std::allocator<std::array<unsigned long,64ul>>::~allocator(&v3);
```

Tables are completely identical to tables from DES standard, so the cipher is implemented correctly. Using this tables we could try to reconstruct context's structure.

```
00000000 Context         struc ; (sizeof=0xA58, mappedto_32)
00000000 pc1             dq 56 dup(?)
000001C0 pc2             dq 48 dup(?)
00000340 keyRotation     dq 16 dup(?)
000003C0 initialPermutation dq 64 dup(?)
000005C0 roundPermutation dq 32 dup(?)
000006C0 finalPermutation dq 64 dup(?)
000008C0 expansion       dq 48 dup(?)
00000A40 sboxVector      dq 3 dup(?)
00000A58 Context         ends
```

### Analysis of context usage

As described above there are two caches: for users and for contexts. Both of them are initialized in the constructor of Frontend class. The second parameter (`8LL`) is max size of the cache.

```c
// Digger::Server::Frontend::Frontend(void)
  Digger::Primitives::Cache<std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>,Digger::Server::User>::Cache(
    this,
    8LL);
  Digger::Primitives::Cache<std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>,Digger::Crypto::Context>::Cache(
    (char *)this + 144,
    8LL);
```

Using this information, we could reconstruct a part of Frontend structure.

```
00000000 Frontend        struc ; (sizeof=0x142, mappedto_33)
00000000 users           db 144 dup(?)
00000090 contexts        db 144 dup(?)
00000120 unknown1        db 32 dup(?)
00000140 unknown2        db ?
00000141 exited          db ?
00000142 Frontend        ends
```

Now look at the `Frontend::Run()` method. This method contains the main I/O loop.

```c
// Digger::Server::Frontend::Run(Frontend *this)
  while ( this->exited != 1 )
  {
    ctx = std::move<Digger::Primitives::Cache<std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>,Digger::Crypto::Context> &>(this->contexts);
    Digger::Primitives::Cache<std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>,Digger::Crypto::Context>::Cache(
      contexts,
      ctx);
    Digger::Server::Backend::Backend(backend, this, contexts);
    while ( this->exited != 1 )
      Digger::Server::Frontend::HandleRequest((Digger::Server::Frontend *)this, (Digger::Server::Backend *)backend);
    Digger::Server::Backend::~Backend((Digger::Server::Backend *)backend);
    Digger::Primitives::Cache<std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>,Digger::Crypto::Context>::~Cache(contexts);
  }}
```

Please notice the exception handler, my version of IDA does not show it (but it obviously exists, we can deduce it from interaction with service).

```
.text:000000000001489B ;   try {
.text:000000000001489B                 call    _ZN6Digger6Server8Frontend13HandleRequestERNS0_7BackendE ; Digger::Server::Frontend::HandleRequest(Digger::Server::Backend &)
.text:000000000001489B ;   } // starts at 1489B
...
---------------------------------------------------------------------------
.text:00000000000148F1 ;   catch(std::exception) // owned by 1489B
.text:00000000000148F1                 endbr64
.text:00000000000148F5                 cmp     rdx, 1
.text:00000000000148F9                 jz      short loc_14900
.text:00000000000148FB                 mov     rbx, rax
.text:00000000000148FE                 jmp     short loc_1497B
.text:0000000000014900 ; ---------------------------------------------------------------------------
```

So, we can rewrite the `Frontend::Run()` method with simple pseudocode.

```c
while (!exited) {
    contexts = std::move(this->Contexts);

    backend = Backend(this->Users, contexts);

    while (!exited) {
        try {
            this->HandleRequest(backend);
        } catch (error) {
            print(error);
            break;
        }
    }
}
```

The main suspicius part is usage of `std::move`. It moves `this->Contexts` into the `Backend` constructor, so `this->Contexts` becomes an empty cache. Then, if the exception occurs in `this->HandleRequest()`, the loop restarts and backend runs with empty contexts cache. At the same time `this->Users` is never changed, so it leads to desynchronization of caches.

If the caches are desynchronized then `Backend::Encrypt()` won't create new context for existing user, instead it will get in from the empty contexts cache. The Cache class is using `std::unordered_map` internally, so accessing an element will return a new element constructed using default constructor.

Let's look at default constructor of Context class.

```c
// Digger::Crypto::Context::Context(Context *this)
{
  qmemcpy(this->pc1, Digger::Crypto::Tables::PC1, sizeof(this->pc1));
  qmemcpy(this->pc2, Digger::Crypto::Tables::PC2, sizeof(this->pc2));
  memset(this->keyRotation, 0, sizeof(this->keyRotation));
  qmemcpy(this->initialPermutation, Digger::Crypto::Tables::INITIAL_PERMUTATION, sizeof(this->initialPermutation));
  qmemcpy(this->roundPermutation, Digger::Crypto::Tables::ROUND_PERMUTATION, sizeof(this->roundPermutation));
  qmemcpy(this->finalPermutation, Digger::Crypto::Tables::FINAL_PERMUTATION, sizeof(this->finalPermutation));
  qmemcpy(this->expansion, Digger::Crypto::Tables::EXPANSION, sizeof(this->expansion));
  return std::vector<std::array<unsigned long,64ul>>::vector(this->sboxVector, &Digger::Crypto::Tables::SBOX);
}
```

See this line of code?

```c
memset(this->keyRotation, 0, sizeof(this->keyRotation));
```

It's looks like a typo, a developer forgot to initialize `KeyRotation` field.

```cpp
Context::Context()
    : PC1(Tables::PC1)
    , PC2(Tables::PC2)
    , InitialPermutation(Tables::INITIAL_PERMUTATION)
    , RoundPermutation(Tables::ROUND_PERMUTATION)
    , FinalPermutation(Tables::FINAL_PERMUTATION)
    , Expansion(Tables::EXPANSION)
    , Sbox(Tables::SBOX) { }
```

In this case the cipher's KEY_ROTATION table will contain all zeroes, and it breaks the indended encryption of DES.

## Trigger

The trigger is pretty simple.

```
> ENCRYPT
username: hacker1337
plaintext (hex): 0000111122223333
ciphertext (hex):
0acae256807f50a9
> ENCRYPT
username: nonexisting
plaintext (hex): badplaintext
error: user does not exist
> ENCRYPT
username: hacker1337
plaintext (hex): 0000111122223333
ciphertext (hex):
7df78d9ae97e16d5
> 
```

See? Ciphertexts are different, because the second ciphertext is incorrect.

## Exploitation

What could we do if the KEY_ROTATION table is zeroed? Let's look at the DES' key schedule.

```
var key // The keys given by the user
var keys[16]
var left, right

// Generate Keys

// PC1 (64 bits to 56 bits) 
key := permutation(key, PC1)
left := (key rightshift 28) and 0xFFFFFFF
right := key and 0xFFFFFFF

for i from 0 to 16 do
	right := right leftrotate KEY_rotation[i]
	left := left leftrotate  KEY_rotation[i]
	var concat := (left leftshift 28) or right
	// PC2 (56bits to 48bits)
	keys[i] := permutation(concat, PC2)
end for
```

If `KEY_rotation[i]` value is always 0, it leads to identical round keys. The key schedule will contain the same key 16 times, so the each round of DES will be encrypted the same way.

This is a sufficient requirement for [slide attack](https://en.wikipedia.org/wiki/Slide_attack). I won't describe the attack in detail, you could read the original paper: [Slide Attacks by Alex Biryukov and David Wagner](https://link.springer.com/content/pdf/10.1007/3-540-48519-8_18.pdf).

The main point of attack is below.

Let `F()` be round encryption function. Then we need to find the pair `(in_block, out_block)` to satisfy the equation `F(in_block) = out_block`. When such blocks are identified, it's trivial to extract `round_key` from the equation. Then just reverse the key schedule algoritm and recover master key of DES.

Since the effective length of DES' master key is 56 bits, we need to guess other 8 bits of key. We could do this by trying all 256 variants of master key and use it as a password. When the original password is found, just output the user's secret.

Something like this:

```python
round_key = slide_attack()
master_key_candidates = recover_possible_master_keys(round_key)

for master_key in master_key_candidates:
    try:
        user = try_login(master_key)
        print(user.secret)
        break
    except InvalidPasswordException:
        continue
```

Example exploit: [sploit.py](/sploits/digger/sploit.py). The attack itself is implemented in [slide.py](/sploits/digger/slide.py).

It does some expensive computations, so run it with [PyPy](https://www.pypy.org/).

```bash
$ time pypy3.10 sploit.py "${HOSTNAME}" 'jKZNCPnMXJ3ooHcesGPagPdfxp' 
trying 32768 blocks more
encrypted 16384 / 32768
encrypted 32768 / 32768
encrypted 16384 / 32768
encrypted 32768 / 32768
found round_key: [1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0]
master_key: [0, 1, 1, 0, 0, 0, 1, -2, 0, 0, 1, 0, 0, 0, 0, -2, 0, 1, 0, 1, 1, 1, 0, -2, 0, 1, 1, 0, 0, 1, 1, -2, 0, 1, 1, 1, 1, 0, 0, -2, 0, 0, 1, 0, 1, 1, 1, -2, 0, 1, 1, 0, 0, 0, 0, -2, 0, 1, 1, 0, 0, 0, 1, -2]
oracle calls: 4 by 16.0 KB
oracle data: 1024.0 KB, 1.0 MB
found key: b'b!]gy.`c'
b'successfully logged in, your secret: ABCDABCDABCDABCDABCDABCDABCDABC='
pypy3.10 sploit.py "${HOSTNAME}" 'jKZNCPnMXJ3ooHcesGPagPdfxp'  2.05s user 0.08s system 28% cpu 7.576 total
```

## Patching

Get rid of `std::move` and pass into `Backend::Backend()` the raw copy of `this->Contexts`.
