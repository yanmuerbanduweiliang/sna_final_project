import math
import numpy as np
import datetiem as dt

def geo_dist(l1,l2):
    return math.sqrt((l2[1]-l1[1])**2 + (l2[0]-l1[0])**2)

def social_feature(s_graph,n1,n2):

    n1_neightbor = s_graph.neighbors(n1)
    n2_neightbor = s_graph.neighbors(n2)
    common_n = set(n1_neightbor).intersection(n2_neightbor)
    
    neiNum1 = len(n1_neightbor)
    neiNum2 = len(n2_neightbor)
    
    if neiNum1+neiNum2 <=0:
        overlap_n = 0
    else:
        overlap_n = len(common_n)*1.0/(neiNum1+neiNum2-len(common_n))
        
    aa_n =0
    for cn in common_n:
        if len(s_graph.neighbors(cn))<=0:#
            continue#
        elif len(s_graph.neighbors(cn)) == 1:#
            aa_n += 100.0#for log 1
        else:
            aa_n = aa_n + 1.0/math.log(len(s_graph.neighbors(cn)))
    
    pa = len(n1_neightbor)*len(n2_neightbor)
    
    return len(common_n),overlap_n,aa_n,pa
    
def place_feature(p_graph,n1,n2):
    n1_place = p_graph.neighbors(n1)
    n2_place = p_graph.neighbors(n2)
    common_p= set(n1_place).intersection(n2_place)
    union_p = set(n1_place).union(n2_place)
    
    pNum1 =len(n1_place)
    pNum2 =len(n2_place)
    
    if pNum1+pNum2 <=0:
        overlap_p = 0
    else:
        overlap_p= len(common_p)*1.0/((pNum1+pNum2)-len(common_p))
    
    aa_ent = 0
    min_ent = 5.0
    aa_p =0
    min_p = 0.0
    
    for place in common_p:
#         compute min_ent
        if (min_ent == 0.0) or (p_graph.node[place]['entropy'] < min_ent):
            min_ent = p_graph.node[place]['entropy']
#         compute min_p
        if (min_p == 0.0) or (p_graph.node[place]['total_checkin'] < min_ent):
            min_p = p_graph.node[place]['total_checkin']
#         count aa_ent
        if p_graph.node[place]['entropy']<=0:
            continue
        else:
            aa_ent = aa_ent + 1.0/p_graph.node[place]['entropy']
#         count aa_p
        if p_graph.node[place]['total_checkin']<=0:
            continue
        else:
            aa_p = aa_p + 1.0/p_graph.node[place]['total_checkin']
    
# compute  w_common_p/w_overlap_p
    
    c1 = list()
    c2 = list()
    for place in union_p:
        if place in n1_place:
            c1.append(p_graph[n1][place]['num_checkin'])
        else:
            c1.append(0)
            
        if place in n2_place:
            c2.append(p_graph[n2][place]['num_checkin'])
        else:
            c2.append(0)
    
    c1 = np.array(c1)
    c2 = np.array(c2)
        
    w_common_p = np.dot(c1,c2)
    
    seDot = (np.dot(c1,c1)*np.dot(c2,c2))**(1/2.0)
    if seDot <= 0:
        w_overlap_p = 0
    else:
        w_overlap_p = np.dot(c1,c2)/seDot
    
    pp = len(n1_place)*len(n2_place)
    
    
    m1 = p_graph.node[n1]['hometown']
    m2 = p_graph.node[n2]['hometown']
    l1 = (p_graph.node[m1]['lat'],p_graph.node[m1]['lng'])
    l2 = (p_graph.node[m2]['lat'],p_graph.node[m2]['lng'])
    
    geodist = geo_dist(l1,l2)
    w_geodist = geodist/((p_graph.edge[n1][m1]['num_checkin'])*(p_graph.edge[n2][m2]['num_checkin']))
    
    if l1[0]==0.0 or l2[0] == 0.0:
        geodist = ""
        w_geodist = ""

    return len(common_p),overlap_p,w_common_p,w_overlap_p,aa_ent,min_ent,aa_p,min_p,pp,geodist,w_geodist


def temporal_place_feature(p_graph, n1, n2):
    # 1. TCS: temporal cosine sim
    # 2. SCR: spatial co-location rate = overlap_p
    # 3. STCR: Spatial top co-location rate
    # 4. SCS: Spatial cosine sim
    # 5. StCR: Spatio-temporal co-location rate
    # 6. StTCR: Spatio-temporal top co-location rate
    # 7. StCS: Spatio-temporal cosine sim

    # get the top N popular place
    popular_places = list()
    fre_places = dict()
    N = 10
    T = 24
    for node in p_graph.nodes():
        if node['type']=='place':
            for neighbor in p_graph.neighbors(node):
                num = len(p_graph[node][neighbor]['checkin_time_list'])
                fre_places[place] = fre_places.get(place, 0)+num
    # sort frequency of places
    s_fre_places= sorted(fre_places.items(), key=lambda d:d[1], reverse = True)
    popular_places = [i[0] for i in s_fre_places[0:10]]

    # build n1, n2 time-place matrix in 24 hours
    n1_tp_matrix = list()
    n2_tp_matrix = list()
    n1_tp_pop_matrix = list()
    n2_tp_pop_matrix = list()
    n1_places = p_graph.neighbors(n1)
    n2_places = p_graph.neighbors(n2)
    # initial n1 and n2 matrix in 24 hours
    for i in range(0, 24):
        n1_tp_matrix.append(dict())
        n2_tp_matrix.append(dict())
        n1_tp_pop_matrix.append(dict())
        n2_tp_pop_matrix.append(dict())
    # build the time-spatial matrix
    for place in n1_places:
        c_list = p_graph.edge[n1][place]['chechin_time_list']
        for time in c_list:
            checkin_time = dt.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")
            n1_tp_matrix[chechin_time.hour][place] = n1_tp_matrix[chechin_time.hour].get(place, 0)+1
    for place in n2_places:
        c_list = p_graph.edge[n2][place]['chechin_time_list']
        for time in c_list:
            checkin_time = dt.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")
            n2_tp_matrix[chechin_time.hour][place] = n2_tp_matrix[chechin_time.hour].get(place, 0)+1
    # build popular time-spatial matrix
    for hour in range(0,24):
        for place in n1_tp_matrix[hour].keys():
            if place in popular_places:
                n1_tp_pop_matrix[hour][place] = n1_tp_matrix[hour][place]
        for place in n2_tp_matrix[hour].keys():
            if place in popular_places:
                n1_tp_pop_matrix[hour][place] = n1_tp_matrix[hour][place]

    # 1. TCS
    TCS = float()
    r1 = list()
    r2 = list()
    for hour in range(0,24):
        r1.append(float(sum(n1_tp_matrix[hour].values())))
        r2.append(float(sum(n2_tp_matrix[hour].values())))
    n1_total_updates = sum(r1)
    n2_total_updates = sum(r2)
    for index, update in enumerate(r1):
        r1[index] = update/n1_total_updates
    for index, update in enumerate(r2):
        r2[index] = update/n2_total_updates
    TCS = np.dot(r1, r2)/((np.dot(r1,r1)*np.dot(r2,r2))**0.5)

    # 3. STCR: 這有點怪怪的
    STCR = float()
    # n = 
    l1 = dict()
    l2 = dict()
    # initial place-fre dict
    for hour in range(0,24):
        for place, fre in n1_tp_pop_matrix[hour].items():
            l1[place] = l1.get(place,0)+fre
            # 其實不用算出fre
        for place, fre in n2_tp_pop_matrix[hour].items():
            l2[place] = l2.get(place,0)+fre
    # from 0 ~ 10
    n = min(len(l1), len(l2))
    if n == 0:
        STCR = 0
    else:
        STCR = len(set(l1.keys()).union(set(l2)))/n

    # 5. StCR: Spatio-temporal co-location rate
    StCR = float()
    for hour in range(0,24):
        n1_places = n1_tp_matrix[hour].keys()
        n2_places = n2_tp_matrix[hour].keys()
        common_p = set(n1_places.intersection(set(n2_places)))
        # union_p = set(n1_places.union(set(n2_places)))
        StCR = StCR+float(len(common_p))/(len(n1_places)+len(n2_places)-len(common_p))
    StCR = StCR/T

    # 6. StTCR: Spatio-temporal top co-location rate
    StTCR = float()
    for hour in range(0,24):
        n1_places = n1_tp_pop_matrix[hour].keys()
        n2_places = n2_tp_pop_matrix[hour].keys()
        common_p = set(n1_places.intersection(set(n2_places)))
        n = min(len(l1), len(l2))
        StTCR = StTCR+float(common_p)/n
    StTCR = StTCR/T

    # 7. StCS: Spatio-temporal cosine sim
    StCS = float()
    for hour in range(0,24):
        n1_place_fre = n1_tp_matrix[hour]
        n2_place_fre = n2_tp_matrix[hour]
        n1_places = n1_place_fre.keys()
        n2_places = n2_place_fre.keys()
        n1_fres = n1_place_fre.values()
        n2_fres = n2_place_fre.values()
        numerator = float()
        for place in n1_places:
            if place in n2_places:
                numerator = numerator+n1_place_fre[place]*n2_place_fre[place]
        denominator = (np.dot(n1_fres, n1_fres)*np.dot(n2_fres, n2_fres))**0.5
        StCS = StCS + numerator/denominator
    StCS = StCS/T

    return TCS, STCR, StCR, StTCR, StCS
        
