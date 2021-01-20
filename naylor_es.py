#!/usr/bin/env python3

from typing import Tuple
from copy import deepcopy
import json
from pprint import pprint
from os import listdir
from os.path import isfile



def linear_inerpolation(point1: tuple[float float], point2: Tuple[float, float], x: int) -> float:
    x1, y1 = point1
    x2, y2 = point2
    return (x2*y1 - x1*y2 + (y2 - y1)*x) / (x2 - x1)


def PE(PH,p_plus,p_minus):
    return PH*p_plus + p_minus*(1-PH)


def PHE(PH,p_plus,p_minus):        
    return p_plus*PH / PE(PH,p_plus,p_minus)



def PHnE(PH,p_plus,p_minus):
    return (1-p_plus)*PH / (1 - PE(PH,p_plus,p_minus))
        

def ask_question(question, answers=range(-5,6)):
    while True:
        answer = int(input(f'{question}: '))
        if answer in answers:
            break
    return answer


class KnowledgeDB:

    def __init__(self, hypotheses, evidences):
        self.hypotheses = deepcopy(hypotheses) 
        self.evidences = deepcopy(evidences) 
        self.calc_evidences_costs()


    def calc_evidences_costs(self):

        for evidence_num in self.evidences.keys():
            cost_sum = 0
            for hypo_name in self.hypotheses:
                hypo = self.hypotheses[hypo_name]
                try:
                    p_plus, p_minus =  hypo['e_triplets'][evidence_num]
                    PH = hypo['PH']
                    cost_item = PHE(PH,p_plus,p_minus) - PHnE(PH,p_plus,p_minus)
                    cost_sum+= abs(cost_item)
                except KeyError:
                    pass
            self.evidences[evidence_num]['cost'] = cost_sum


    @property
    def maxcost_evidence_num(self):
        maxcost=0
        res=0
        for i in self.evidences.keys():
            if self.evidences[i]['cost']>=maxcost:
                res=i
                maxcost=self.evidences[i]['cost']
        return res




    def recalc_PH(self,evidence_num,R):
        if R:
            for hypo_name in self.hypotheses:
                hypo = self.hypotheses[hypo_name]
                try:
                    p_plus, p_minus =  hypo['e_triplets'][evidence_num]
                    edge_func, edge_r = (PHE,5) if R > 0 else (PHnE,-5)
                    edge_val = edge_func(hypo['PH'],p_plus,p_minus)
                    phr = linear_inerpolation((edge_r,edge_val), (0,hypo['PH']), R)
                    hypo['PH'] = phr
                except KeyError:
                    pass
        del self.evidences[evidence_num]


    def calc_P_max_min(self):

        for hypo in self.hypotheses.values():
            hypo['P_max'] = hypo['P_min'] = hypo['PH']
            for evidence_num in hypo['e_triplets']:
                if evidence_num not in self.evidences:
                    continue
                p_plus,p_minus = hypo['e_triplets'][evidence_num]
                ph = hypo['P_max']
                hypo['P_max'] = max(PHE(ph,p_plus,p_minus), PHnE(ph,p_plus,p_minus), ph)
                ph = hypo['P_min']
                hypo['P_min'] = min(PHE(ph,p_plus,p_minus), PHnE(ph,p_plus,p_minus), ph)


    # returns resulting best hypos if it exists
    def get_winner_hypos(self) -> List:
        max_of_mins_hypo = max((hypo_name for hypo_name in self.hypotheses),
            key=lambda x:self.hypotheses[x]['P_min'])
        PM = self.hypotheses[max_of_mins_hypo]['P_min']
        for hypo_name in self.hypotheses:
            hypo=self.hypotheses[hypo_name]
            if hypo['P_max'] > PM and hypo_name != max_of_mins_hypo:
                return []
        max_ph = max(hypo['PH'] for hypo in self.hypotheses.values())
        res=[]
        for hypo_name in self.hypotheses:
            hypo=self.hypotheses[hypo_name]
            if hypo['PH']==max_ph:
                res.append(hypo_name)
        return res

    def get_all_hypos_with_ph(self):
        return ((hypo,self.hypotheses[hypo]['PH']) for hypo in self.hypotheses)




if __name__=="__main__":
    dbs = tuple(f for f in listdir('.') if isfile(f) \
         and f.startswith('kdb') and f.endswith('.json'))
    if len(dbs) == 1:
        db = dbs[0]
    else:
        for i in range(len(dbs)):
            print (i+1 ,'-', dbs[i])
        dbnum = ask_question('Please choose the knowledge DB:',range(1,len(dbs)+1)) - 1
        db = dbs[dbnum]

    with open(db,'r') as f:
        json_db = json.load(f)
    hypos = json_db['hypotheses']
    kdb = KnowledgeDB(hypos,json_db['evidences'])
    print ("You need to answer with an integer from -5 to 5\n"
        " 5 - totally agree,\n-5 - totally disagree,\n 0 - I don't know\n")
    while True:
        kdb.calc_evidences_costs()
        men = kdb.maxcost_evidence_num
        R = ask_question(kdb.evidences[men]['question'])
        kdb.recalc_PH(men, R)
        sorted_hypos = sorted(kdb.get_all_hypos_with_ph(), key=lambda x:x[1], reverse=True)
        print ('\n'.join(f'{h} : {p:.2f}' for (h,p) in sorted_hypos))
        kdb.calc_P_max_min()
        winners = kdb.get_winner_hypos()
        if winners:
            break
    print ('\nWinners:')
    for hypo_name in winners:
        print (hypo_name, f"{kdb.hypotheses[hypo_name]['PH']:.2f}")




