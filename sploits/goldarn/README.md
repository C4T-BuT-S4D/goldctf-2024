# Goldarn

Goldarn is an online stack-based language interpreter. The service allows users to access a REPL and use any command available in language.

Flags were stored in content of randomly named files.

Service is written in Rust and allows reading and writing of any file on the system. Also a C-wrapper is used to apply seccomp and to change uid and gid to `1337 + rand[0, 256)`. The [gotty](https://github.com/yudai/gotty) binary was used to interact with REPL via websockets.

## Home overriding

### Gotty config exploit

Service is using gotty v1.0.1 to run `cargo run` [command](../../services/goldarn/run_gotty.sh) on each connection. The gotty command was run by a user with uid 1337 that had an existing home directory created in [Dockerfile](../../services/goldarn/Dockerfile). The cargo command was run by a user with uid `1337 + rand[0, 256)` which that with 1/256 probability we can write and read files in 1337 user home directory. Lucky for us gotty supports [configuration files](https://github.com/yudai/gotty/blob/v1.0.1/.gotty) in home directory. One interesting option is `permit_arguments` which allows user to pass additional arguments to underlying binary (in our case it's cargo). We can use this to overwrite path to Cargo.toml via `--manifest-path` and run binary from Rust project located in different directory. The last step is to find directory we can write to and craft a complete Rust project structure in it (Cargo.toml and one source file). `/tmp` directory can be used only once - since cargo doesn't allow overriding Cargo.toml file name and service doesn't allow overwriting files, only appending. At this moment we can see that C-wrapper creates temporary directory for each execution and it can be used for explotation. Exploit reads `/proc/self/environ` file to find location of this directory via `LD_LIBRARY_PATH` env variable.

### Cargo config exploit (unintended, from [Superflat](https://ctftime.org/team/274071/) team)

```
We (Superflat) used a different exploit for goldarn: checker setuids to 1337+random_byte, so its possible for uid to stay 1337 (ctf user). This user can write to $CARGO_HOME/config.toml and use it to overwrite runner for the default triple
```

### Fix

Change `setuid(1337 + rand[0, 256))` to `setuid(1337 + rand[1, 256))` so overriding of home directory become impossible.