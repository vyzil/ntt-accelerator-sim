#!/bin/bash

# 테스트 파라미터
START_IDX=0
STRIDE_EXP=0
COUNT=512
IS_WRITE=0

# 트레이스 생성
./generate "$START_IDX" "$STRIDE_EXP" "$COUNT" "$IS_WRITE" 1> /dev/null

# 시뮬레이션 실행
./test
# ./test -D issue