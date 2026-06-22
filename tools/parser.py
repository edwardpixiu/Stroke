from datetime import datetime

def timestamp_parser(rawtime):
    """
    Parser the rawtime stmap in Marker file into standard format "%Y%m%d%H%M%S%f"
    
    Args:
        rawtime (str): raw timestmap
    Returns:
        standard format (str): datetime.timestmap
        
    """
    dt = datetime.strptime(rawtime, "%Y%m%d%H%M%S%f")
    
    return dt, dt.timestamp()
        
def get_timetree(recorder_1:str):
    
    """
    Parser the Brainvision Data Marker File into Dict format time tree
    
    Args:
        recorder_1 (str): the raw marker file .vhdr
        Returns: 
        timetree (dict): the precise timetree dictionary, each timestmap within two format:\n
        standard: xxxx / xx / xx / xx / xxxxx (Y/M/D/H/S/Us) 
        timestmap: datetime.stmap
    """
  
    with open(recorder_1, encoding='utf-8', mode='r') as R1:
        R1_data = R1.read()
        
    timestmap_list = R1_data.split('\n')
    
    potential_list = [i for i in timestmap_list if i.startswith('Mk')]
    
    # print(potential_list)
    timetree = {}
    mcount = 0
    
    for mk in potential_list:
        mk_content = mk.split('=')[-1].split(',')
        if mk_content[0] == 'New Segment':
            mktime, mktimestamp = timestamp_parser(mk_content[-1])
            timetree["start_0"] = {
                "time":mktime,
                "stamp":mktimestamp
            }
        elif mk_content[0] == 'Stimulus':
            mcount += 1
            timetree["marker_"+str(mcount)] = {
                "marker":[i for i in mk_content[1].split(" ") if i != ""],
                "index":int(mk_content[2])
            }
            
    print(timetree)
    
    return timetree
            
# if __name__ == "__main__":
    
#     recorder_1 = r'rawdata/test03-20260617/huangweidong_3.vmrk'  # marker text
    
#     recorder_2 = r'rawdata/test03-20260617/huangweidong_3.vhdr' # marker header
    
    
#     get_timetree(R1_data_list)
    