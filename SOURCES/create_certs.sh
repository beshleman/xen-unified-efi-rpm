#!/bin/bash

# This script generates a set of auth variables that can be used to test secure boot.

set -e

CERTS_DIR=test_certs
KEY="${CERTS_DIR}/test.key"
PEM="${CERTS_DIR}/test.pem"
DER="${CERTS_DIR}/test.der"
DB="${CERTS_DIR}/db.auth"
KEK="${CERTS_DIR}/KEK.auth"
PK="${CERTS_DIR}/PK.auth"

mkdir -p ${CERTS_DIR}

openssl req \
    -newkey rsa:4096 -nodes -keyout "${KEY}" \
    -new -x509 -sha256 -days 3650   \
    -subj "/CN=Test Owner/" -out "${PEM}"

openssl x509 -outform DER -in "${PEM}" -out "${DER}"

/opt/xensource/libexec/create-auth db ${DB} ${PEM} 

# Create dummy KEK and PK
/opt/xensource/libexec/create-auth KEK ${KEK} ${PEM}
# PK should be self-signed
/opt/xensource/libexec/create-auth -c ${PEM} -k ${KEY} PK ${PK} ${PEM} 

cat >> ${CERTS_DIR}/README.md <<END
# Test Secure Boot Certificates

Files:
* db.auth
  * A valid EFI auth file that may be installed onto a Secure Boot enabled host
    as the db file that enables the package to be installed on test systems
    with SB enabled.
* KEK.auth and PK.auth
  * These are the same cert as the db.auth. Just repackaged as KEK and PK.
* test.{der,pem}
  * The test certificate (in DER and PEM) used to sign the binaries and create
    the EFI auth file.
* test.key
  * The private key used in conjunction with the DER/PEM certs to sign the
    binaries.
END


tar cvf ${CERTS_DIR}.tar ${CERTS_DIR}
rm -rf ${CERTS_DIR}

echo "Certificates generated in tarball: ${CERTS_DIR}.tar"
