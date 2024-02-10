# Nugget

Nugget is a data storage service with backup functionality. Multiple commands are available:

- `project` creates a new project (a directory) with user-specified password
- `upload` uploads a tar archive to the current project that's repacked into zip archive
- `list` lists files inside zip archives
- `download` downloads the files from zip archives
- `delete` deletes the archive
- `job` accepts a "backup job definition" consisting of multiple files (possibly from other projects) and packs them
  into zip archive. If the file is from another project, it's encrypted using the project's password.

Players were also given a decently fast solver for the captcha required by `upload` and `job` commands.
To compile it, one can run

```
cd ../../services/nugget
CGO_ENABLED=0 go build -o ../../sploits/nugget/captcha_solver ./cmd/captcha/main.go
cd ../../sploits/nugget
```

This service was actually a rewritten Artifact Bunker task from DefCon Qualifier 2023. We've found this
beautiful race condition during the competition, but unfortunately the infrastructure was set up
to prevent any kind of race condition exploitation for this task.

## Vulnerabilities

### Intended

#### TLDR

The flags are stored in plain text in the hidden tar archive created when running `job`. To leak them, a race condition
between the `job` and `upload` can be used to overwrite the start of the `tar` archive with a carefully crafted tar
header.

#### Details

- `upload` doesn't remove the temporary `tar` archive even if it's incorrect. It allows the attacker to upload arbitrary
  files.
- `upload` doesn't check if the name is hidden (starts with a dot), which allows us to upload the .<job_name>.tar file
  while
  there's a currently running `job` writing to this file.

Funny enough, linux allows to open one file for writing from two clients simultaneously. Both clients use O_TRUNC, so
the
data stored in the file before opening is removed, but consider the following situation:

1. `job` opens file .build.tar for writing, writes X bytes to it
2. `upload` opens file .build.tar for writing, writes Y < X bytes to it
3. `job` goes on writing to file

In that case, after `job` goes on writing in step 3, the file is padded with zero-bytes up to length X and has the
following structure:

```
<Y>     bytes uploaded
<X - Y> zero bytes
<...>   leftover job data
```

If we include the flag in the job, it will be stored in the tar archive in plaintext.

Having learned all that, we can use the carefully-constructed tar header (we'll call it "start header") at the start of
the archive to consume
the zero-bytes, and second tar header (we'll call it "jump" header) right after that to leak the data after it.

To craft it, one can:

- upload some padding archives first (content doesn't matter, just the length)
- upload jump header
- run the job containing 2000 padding files, jump header, flag and some more padding files (in this order exactly)
- (at the same time as the job) upload the start header

In the end, we'll have the following archive:

```
<start header consuming 2000 padding files>
<zero-bytes>
<some padding files>
<jump header consuming flag file and some padding>
<flag file in plaintext>
<some more padding files>
```

When it's converted to zip, we'll have flag file content in plain text in the "jump" file
and can download it by simply running the `download` command.

### Unintended

Unfortunately, there was a quite trivial path traversal bug in the `job` command
that allowed to include the flag file in the job:

```json
{
  "job": {
    "steps": [
      {
        "name": "some-job",
        "artifacts": [
          {
            "source_project": "",
            "source": "../<flag-id>",
            "destination": "<some-file>"
          }
        ]
      }
    ]
  }
}
```

Kudos to Bushwhackers for finding it and first-blooding this service.
