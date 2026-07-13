#ifndef SPY_SSZ_DECODE_STATUS_H
#define SPY_SSZ_DECODE_STATUS_H

typedef enum {
    SPY_SSZ_DECODE_UNRECOGNIZED_FIELD = -1,
    SPY_SSZ_DECODE_MALFORMED_INPUT = 0,
    SPY_SSZ_DECODE_VALID = 1,
} spy_ssz_decode_status;

enum {
    SPY_SSZ_ERROR_POSITION_UNSET = -1,
};

#endif
