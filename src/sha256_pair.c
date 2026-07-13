#if defined(__linux__) && !defined(_POSIX_C_SOURCE)
#define _POSIX_C_SOURCE 200809L
#endif

#include <stdint.h>
#include <string.h>

#include "ssz_kernels.h"

#if defined(__APPLE__)
#include <CommonCrypto/CommonDigest.h>
#elif defined(__linux__)
#include <dlfcn.h>
#endif

/* SHA-256 specialized for SSZ's fixed 64-byte pair hash. */
static inline uint32_t rotate_right(uint32_t value, uint32_t shift) {
    return (value >> shift) | (value << (32U - shift));
}

static void compress_sha256(uint32_t state[8], const uint8_t block[64]) {
    static const uint32_t constants[64] = {
        0x428a2f98U, 0x71374491U, 0xb5c0fbcfU, 0xe9b5dba5U,
        0x3956c25bU, 0x59f111f1U, 0x923f82a4U, 0xab1c5ed5U,
        0xd807aa98U, 0x12835b01U, 0x243185beU, 0x550c7dc3U,
        0x72be5d74U, 0x80deb1feU, 0x9bdc06a7U, 0xc19bf174U,
        0xe49b69c1U, 0xefbe4786U, 0x0fc19dc6U, 0x240ca1ccU,
        0x2de92c6fU, 0x4a7484aaU, 0x5cb0a9dcU, 0x76f988daU,
        0x983e5152U, 0xa831c66dU, 0xb00327c8U, 0xbf597fc7U,
        0xc6e00bf3U, 0xd5a79147U, 0x06ca6351U, 0x14292967U,
        0x27b70a85U, 0x2e1b2138U, 0x4d2c6dfcU, 0x53380d13U,
        0x650a7354U, 0x766a0abbU, 0x81c2c92eU, 0x92722c85U,
        0xa2bfe8a1U, 0xa81a664bU, 0xc24b8b70U, 0xc76c51a3U,
        0xd192e819U, 0xd6990624U, 0xf40e3585U, 0x106aa070U,
        0x19a4c116U, 0x1e376c08U, 0x2748774cU, 0x34b0bcb5U,
        0x391c0cb3U, 0x4ed8aa4aU, 0x5b9cca4fU, 0x682e6ff3U,
        0x748f82eeU, 0x78a5636fU, 0x84c87814U, 0x8cc70208U,
        0x90befffaU, 0xa4506cebU, 0xbef9a3f7U, 0xc67178f2U,
    };
    uint32_t words[64];
    uint32_t a, b, c, d, e, f, g, h;
    uint32_t i;

    for (i = 0; i < 16; i++) {
        uint32_t offset = i * 4U;
        words[i] = ((uint32_t)block[offset] << 24U)
            | ((uint32_t)block[offset + 1U] << 16U)
            | ((uint32_t)block[offset + 2U] << 8U)
            | (uint32_t)block[offset + 3U];
    }
    for (i = 16; i < 64; i++) {
        uint32_t x = words[i - 15U];
        uint32_t y = words[i - 2U];
        uint32_t s0 = rotate_right(x, 7U) ^ rotate_right(x, 18U) ^ (x >> 3U);
        uint32_t s1 = rotate_right(y, 17U) ^ rotate_right(y, 19U) ^ (y >> 10U);
        words[i] = words[i - 16U] + s0 + words[i - 7U] + s1;
    }

    a = state[0]; b = state[1]; c = state[2]; d = state[3];
    e = state[4]; f = state[5]; g = state[6]; h = state[7];
    for (i = 0; i < 64; i++) {
        uint32_t sum1 = rotate_right(e, 6U) ^ rotate_right(e, 11U)
            ^ rotate_right(e, 25U);
        uint32_t choice = (e & f) ^ ((~e) & g);
        uint32_t temporary1 = h + sum1 + choice + constants[i] + words[i];
        uint32_t sum0 = rotate_right(a, 2U) ^ rotate_right(a, 13U)
            ^ rotate_right(a, 22U);
        uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
        uint32_t temporary2 = sum0 + majority;
        h = g; g = f; f = e; e = d + temporary1;
        d = c; c = b; b = a; a = temporary1 + temporary2;
    }
    state[0] += a; state[1] += b; state[2] += c; state[3] += d;
    state[4] += e; state[5] += f; state[6] += g; state[7] += h;
}

#if defined(__linux__)
typedef struct {
    uint32_t state[8];
    uint32_t bit_count_low;
    uint32_t bit_count_high;
    uint32_t data[16];
    unsigned int data_length;
    unsigned int digest_length;
} spy_openssl_sha256_context;

typedef void (*spy_openssl_sha256_transform)(
    spy_openssl_sha256_context *, const unsigned char *
);

static spy_openssl_sha256_transform spy_linux_sha256_transform(void) {
    static spy_openssl_sha256_transform transform = NULL;
    static int initialized = 0;
    static void *library = NULL;
    if (!initialized) {
        transform = (spy_openssl_sha256_transform)dlsym(
            RTLD_DEFAULT, "SHA256_Transform"
        );
        if (transform == NULL) {
            library = dlopen("libcrypto.so.3", RTLD_LAZY | RTLD_LOCAL);
            if (library == NULL)
                library = dlopen("libcrypto.so.1.1", RTLD_LAZY | RTLD_LOCAL);
            if (library != NULL)
                transform = (spy_openssl_sha256_transform)dlsym(
                    library, "SHA256_Transform"
                );
        }
        initialized = 1;
    }
    return transform;
}
#endif

void spy_sha256_pair(const uint8_t *source, uint8_t *output) {
#if defined(__APPLE__)
    CC_SHA256(source, 64, output);
#else
    uint32_t state[8] = {
        0x6a09e667U, 0xbb67ae85U, 0x3c6ef372U, 0xa54ff53aU,
        0x510e527fU, 0x9b05688cU, 0x1f83d9abU, 0x5be0cd19U,
    };
    uint8_t padding[64] = {0};
    uint32_t i;

    padding[0] = 0x80U;
    padding[62] = 0x02U;
#if defined(__linux__)
    spy_openssl_sha256_transform transform = spy_linux_sha256_transform();
    if (transform != NULL) {
        spy_openssl_sha256_context context = {0};
        memcpy(context.state, state, sizeof(state));
        context.digest_length = 32;
        transform(&context, source);
        transform(&context, padding);
        memcpy(state, context.state, sizeof(state));
    } else {
        compress_sha256(state, source);
        compress_sha256(state, padding);
    }
#else
    compress_sha256(state, source);
    compress_sha256(state, padding);
#endif
    for (i = 0; i < 8; i++) {
        uint32_t value = state[i];
        uint32_t offset = i * 4U;
        output[offset] = (uint8_t)(value >> 24U);
        output[offset + 1U] = (uint8_t)(value >> 16U);
        output[offset + 2U] = (uint8_t)(value >> 8U);
        output[offset + 3U] = (uint8_t)value;
    }
#endif
}

void spy_ssz_kernels$hash_pair_into(
    spy_BytesObject *source,
    int32_t source_offset,
    spy_BytesObject *output,
    int32_t output_offset,
    spy_BytesObject *unused_state,
    spy_BytesObject *unused_schedule
) {
    (void)unused_state;
    (void)unused_schedule;
    spy_sha256_pair(
        source->data.p + source_offset,
        output->data.p + output_offset
    );
}
