# Cell

Cells is an online, real-time spreadsheet editor. The service allows clients to upload and create XLSX files and edit them: all the changes made to the file will be broadcasted to other file viewers/editors in real time.

Flags were stored in the spreadsheet names (sheet titles in Excel).

Service is using PHP as an application backend and Centrifugo: https://centrifugal.dev/ to handle websockets (real-time) communications. However, Centrifugo proxies all the relevant requests (subscribe, RPC) to the PHP backend, so all the authorization and application logic is handled by PHP code.

## Internals

Internally, the service logic is relatively simple. A user-created or uploaded file is identified by a randomly generated unique ID (UUID). The service also generates two access tokens: one for reading the file contents and one for modifying the file content.

For a sheet with the `ID = aaaaaaaa-bbbb-cccc`, three files will be generated:

1. `/data/user-files/aaaaaaaa-bbbb-cccc` -> file content.
2. `/data/acls/aaaaaaaa-bbbb-cccc.read` -> read token.
3. `/data/acls/aaaaaaaa-bbbb-cccc.modify` -> write token.

Keep in mind that for an ID of length X, the path lengths are as follows:

- `len(path_to_content) = X+17`
- `len(path_to_read_token) = X+16`
- `len(path_to_write_token) = X+18`

The algorithm for both read and modify operations is similar. To check if the user can read/modify the file, the service performs these steps:

1. Computes the path to the content file (`/data/user-files/$sheetId`).
2. Checks if the content file exists using the PHP `file_exists` function.
3. Computes the path to the token file (`/data/acls/$sheetId.read` or `/data/acls/$sheetId.modify`).
4. Checks if the token file exists using the PHP `file_exists` function.
5. Reads the token from the file using the PHP `file_get_contents` function.
6. Checks if the file contents are equal to the provided `$token` using the `==` operator.

Note that the `$sheetId` and `$token` are provided by the user and never validated, so the user has full control over them.

### Vulnerability (PHP off-by-one + type juggling)

The PHP function `file_get_contents` returns `false` if the file does not exist. Comparing `false` with an empty string `""` using the `==` operator results in `true`.

This shouldn't be an issue here, as the service checks for file existence using `file_exists` first. However, PHP has a surprising behavior: [https://github.com/php/php-src/issues/9903](https://github.com/php/php-src/issues/9903)

**TLDR:** `file_exists` can handle file paths of length `PHP_MAXPATHLEN-1`, but `file_get_contents` cannot.

Knowing this, we can construct a filename such that `file_exists` returns `true` but `file_get_contents` returns `false`. This involves modifying the `sheetId` so that the path to the token file has a length of `PHP_MAXPATHLEN-1`.

The problem is that we can't simply read files using this bug because of the additional check for content file existence. To bypass read token validation, we'd need `len($sheetId) = PHP_MAXPATHLEN-16 - 1`. But in this case, the path to the content file would be 1 character longer, causing `file_exists` to fail.

However, this does work for bypassing the `modify_token`. So, how can we leak flags if we can only modify files?

We can trigger an error that leaks information. PHPSpreadsheet is an interesting library: it computes formulas when saving a file and prints the sheet name in the error if an exception occurs during computation. With this in mind, we just need to send a `modify` request that triggers the error.

The provided exploit uses the `WEBSERVICE` function, which throws an error because HTTP client is not configured: [https://github.com/PHPOffice/PhpSpreadsheet/blob/d6204975114cdc7ee0570fb6a658cc4bc1adca39/src/PhpSpreadsheet/Settings.php#L174](https://github.com/PHPOffice/PhpSpreadsheet/blob/d6204975114cdc7ee0570fb6a658cc4bc1adca39/src/PhpSpreadsheet/Settings.php#L174).

**Full exploit: ./modify_sheet.py**

### Fix

There are multiple fix options:

1. Do not return errors.
2. Fix the type juggling (use `===` or check for `false`).
3. Modify the folder structure.

