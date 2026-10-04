#ifndef GENRANDOM
#define GENRANDOM

#include "genrandom.h"
#include <cstdlib>

genrandom::genrandom() {}

//LargeVis gsl back[0,1)
void genrandom::init_gsl (){
    const gsl_rng_type * T;
    float u;
    gsl_rng_env_setup();
    T = gsl_rng_default;
    r = gsl_rng_alloc(T);
    // MCSBN : graine fixe si GSL_RNG_SEED est defini (lu par gsl_rng_env_setup),
    // pour un layout reproductible ; sinon graine aleatoire comme a l'origine.
    if (getenv("GSL_RNG_SEED")) gsl_rng_set(r, gsl_rng_default_seed);
    else gsl_rng_set(r, time (NULL) * getpid());
    //gsl_rng_set(r, 314159265);
}

float genrandom::gslRandom() {
    float u = gsl_rng_uniform (r);
    return u;
}

#endif
