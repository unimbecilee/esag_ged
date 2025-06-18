from AppFlask import create_app

app = create_app()

print("=== ROUTES DE VALIDATION WORKFLOW ===")
for rule in app.url_map.iter_rules():
    if 'validation-workflow' in rule.rule.lower():
        methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
        print(f"{rule.rule:<50} [{methods}] -> {rule.endpoint}")

print("\n=== TOUTES LES ROUTES API ===")
api_routes = []
for rule in app.url_map.iter_rules():
    if rule.rule.startswith('/api/'):
        methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
        api_routes.append((rule.rule, methods, rule.endpoint))

api_routes.sort()
for route, methods, endpoint in api_routes:
    print(f"{route:<50} [{methods}] -> {endpoint}") 