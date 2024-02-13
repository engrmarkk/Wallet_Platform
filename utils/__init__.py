def determine_purchase_type(service_id):
    if service_id in ["mtn", "glo", "etisalat", "airtel"]:
        return "airtime"
    elif service_id in ["mtn-data", "glo-data", "etisalat-data", "airtel-data", "smiles", "spectranet"]:
        return "data"
    elif service_id in ["ikedc", "ibedc"]:
        return "electricity"
    elif service_id in ["cable"]:
        return "cable"
    else:
        return None
