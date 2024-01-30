import json

score = {}

users = {
    275370983378911233 : 78,
    190672357143216130 : 151,
    527906663903002625 : 170,
    446091432093024266 : 27,
    274735046223724545 : 167,
    252219075705438209 : 73,
    223100188414312449 : 180,
    270740019193315338 : 194,
    262746111901564928 : 103,
    409037589824405516 : 33,
    319124406335176704 : 1,
    189957536009551873 : 41,
    469386240718929921 : 13
}
score[556672124559949835] = {}
for id in users:
    score[556672124559949835][id] = {}
    score[556672124559949835][id]["score"] = users[id]
    score[556672124559949835][id]["given"] = 0
    score[556672124559949835][id]["self"] = 0
with open("clownScore.json", "w") as oFile:
    json.dump(score, oFile)