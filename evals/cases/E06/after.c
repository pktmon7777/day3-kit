#include <stdio.h>
#include <stdlib.h>
#include "compute.h"

int sum_values(const int *values, int count)
{
    int sum = 0;
    for (int i = 0; i < count; i++) {
        sum += values[i];
    }
    return sum;
}

int average(const int *values, int count)
{
    if (count <= 0) {
        return 0;
    }
    return sum_values(values, count) / count;
}

int *copy_values(const int *values, int count)
{
    int *buf = malloc(sizeof(int) * (size_t)count);
    if (buf == NULL) {
        return NULL;
    }
    for (int i = 0; i < count; i++) {
        buf[i] = values[i];
    }
    return buf;
}

void fill_history(int history[MAX_HISTORY], int value)
{
    for (int i = 0; i < MAX_HISTORY; i++) {
        history[i] = value;
    }
}

int apply_discount(int price, int percent)
{
    return price - (price * percent) / PERCENT_BASE;
}

int clamp_percent(int percent)
{
    if (percent < 0) {
        return 0;
    }
    if (percent > PERCENT_BASE) {
        return PERCENT_BASE;
    }
    return percent;
}
