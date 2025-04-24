#ifndef SCOREENGINE_H
#define SCOREENGINE_H

#include "clientprofile.h"
#include "scoreweights.h"

class ScoreEngine {
public:
    static double calculateScore(const ClientProfile& client, const ScoreWeights& weights); // Add this
};

#endif // SCOREENGINE_H
