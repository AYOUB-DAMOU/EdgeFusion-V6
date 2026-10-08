def apply_operation(value, operation, op_val):
    """
    Applique une opération mathématique sur une valeur.
    Retourne le résultat float ou 0 en cas d'erreur.
    """
    try:
        if operation == "+":
            return value + op_val
        elif operation == "-":
            return value - op_val
        elif operation == "*":
            return value * op_val
        elif operation == "/":
            if op_val == 0:
                print("[OPERATION] Division par zéro → 0")
                return 0
            return value / op_val
        else:
            print(f"[OPERATION] Opération inconnue '{operation}' → valeur inchangée")
            return value
    except Exception as e:
        print(f"[OPERATION] Erreur calcul : {e}")
        return 0


def apply_all_operations(data, tag_operations, tag_mapping):
    """
    Applique les opérations mathématiques à tous les tags concernés.
    Retourne data modifié (0 en cas d'erreur sur un tag).
    """
    for tag, op_info in tag_operations.items():
        mqtt_key = tag_mapping.get(tag, f"s={tag.split('=')[-1]}")

        if mqtt_key not in data:
            continue

        current_value = data[mqtt_key]
        operation     = op_info["op"]
        op_value_str  = op_info["val"]

        # Résoudre l'opérande : nombre fixe ou node_id d'un autre tag ?
        try:
            op_val = float(op_value_str)
        except ValueError:
            other_mqtt_key = tag_mapping.get(
                op_value_str,
                f"s={op_value_str.split('=')[-1]}"
            )
            other_value = data.get(other_mqtt_key)
            if other_value is None:
                print(f"[OPERATION] Tag référencé '{op_value_str}' introuvable → 0")
                data[mqtt_key] = 0
                continue
            try:
                op_val = float(other_value)
            except (ValueError, TypeError):
                data[mqtt_key] = 0
                continue

        try:
            data[mqtt_key] = apply_operation(float(current_value), operation, op_val)
        except (ValueError, TypeError):
            data[mqtt_key] = 0

    return data
