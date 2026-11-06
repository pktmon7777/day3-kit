/* pre-deploy test - deploy.yml runs this after the build. Any failure exits non-zero and stops the deploy. */
#include <stdio.h>
#include <stdlib.h>
#include "compute.h"

static int failed = 0;
#define CHECK(name, cond) do { if (cond) { printf("PASS %s\n", name); } else { printf("FAIL %s\n", name); failed++; } } while (0)

int main(void)
{
    int v[] = {10, 20, 30};
    int h[MAX_HISTORY];
    int *c;

    CHECK("sum_values 10+20+30 = 60", sum_values(v, 3) == 60);
    CHECK("average 10,20,30 = 20", average(v, 3) == 20);
    CHECK("average count 0 = 0 (div-by-zero guard)", average(v, 0) == 0);
    c = copy_values(v, 3);
    CHECK("copy_values same values", c != NULL && c[0] == 10 && c[2] == 30);
    free(c);
    fill_history(h, 7);
    CHECK("fill_history all 7", h[0] == 7 && h[MAX_HISTORY - 1] == 7);
    CHECK("apply_discount 1000 10% = 900", apply_discount(1000, 10) == 900);

    printf("%s - failed %d\n", failed ? "TEST FAIL" : "TEST PASS", failed);
    return failed ? 1 : 0;
}
