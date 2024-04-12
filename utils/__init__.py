def determine_purchase_type(service_id):
    if service_id.lower() in ["mtn", "glo", "etisalat", "airtel"]:
        return "airtime"
    elif service_id.lower() in ["mtn-data", "glo-data", "etisalat-data", "airtel-data", "smiles", "spectranet"]:
        return "data"
    elif service_id.lower() in ["ikeja-electric", "eko-electric", "abuja-electric", "kano-electric", "portharcourt-electric",
                                "jos-electric", "kaduna-electric", "enugu-electric", "ibadan-electric", "benin-electric",
                                "aba-electric", "yola-electric"]:
        return "electricity"
    elif service_id.lower() in ["dstv", "gotv", "startimes", "showmax"]:
        return "cable"
    else:
        return None
