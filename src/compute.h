#ifndef COMPUTE_H
#define COMPUTE_H

#define MAX_HISTORY 16
#define PERCENT_BASE 100

int sum_values(const int *values, int count);
int average(const int *values, int count);
int *copy_values(const int *values, int count);
void fill_history(int history[MAX_HISTORY], int value);
int apply_discount(int price, int percent);

#endif
