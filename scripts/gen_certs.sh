#!/bin/bash
# Generate self-signed certificates for mutual TLS authentication

CERTS_DIR="certs"
mkdir -p $CERTS_DIR

echo "Generating CA..."
openssl req -new -x509 -days 365 -nodes -text -out ${CERTS_DIR}/ca_cert.pem -keyout ${CERTS_DIR}/ca_key.pem -subj "/CN=Quantum-Zero-Trust-CA"

echo "Generating Alice certificate..."
openssl req -new -nodes -text -out ${CERTS_DIR}/alice.req -keyout ${CERTS_DIR}/alice_key.pem -subj "/CN=Alice"
chmod -R 770 ${CERTS_DIR}/alice_key.pem
openssl x509 -req -in ${CERTS_DIR}/alice.req -text -days 365 -CA ${CERTS_DIR}/ca_cert.pem -CAkey ${CERTS_DIR}/ca_key.pem -CAcreateserial -out ${CERTS_DIR}/alice_cert.pem

echo "Generating Bob certificate..."
openssl req -new -nodes -text -out ${CERTS_DIR}/bob.req -keyout ${CERTS_DIR}/bob_key.pem -subj "/CN=Bob"
chmod -R 770 ${CERTS_DIR}/bob_key.pem
openssl x509 -req -in ${CERTS_DIR}/bob.req -text -days 365 -CA ${CERTS_DIR}/ca_cert.pem -CAkey ${CERTS_DIR}/ca_key.pem -CAcreateserial -out ${CERTS_DIR}/bob_cert.pem

rm ${CERTS_DIR}/*.req

echo "Certificates generated in ${CERTS_DIR}/"
