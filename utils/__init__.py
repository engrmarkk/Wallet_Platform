def determine_purchase_type(service_id):
    if service_id.lower() in ["mtn", "glo", "etisalat", "airtel"]:
        return "airtime"
    elif service_id.lower() in ["mtn-data", "glo-data", "etisalat-data", "airtel-data", "smiles", "spectranet"]:
        return "data"
    elif service_id.lower() in ["ikedc", "ibedc", "ekedc", "kedco", "phed", "jed", "aedc", "eedc", "bedc", "aba"]:
        return "electricity"
    elif service_id.lower() in ["dstv", "gotv", "startimes", "showmax"]:
        return "cable"
    else:
        return None
