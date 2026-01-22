# Template Scripts

Este directorio contiene scripts y herramientas para trabajar con el template del proyecto.

## Estructura

```
.template/
├── setup/          # Scripts para configurar un nuevo proyecto desde el template
└── flows/          # Scripts para implementar flujos de datos
```

## Setup de Proyecto

Scripts para configurar un nuevo proyecto desde el template. Automatiza el renombrado de directorios, actualización de imports, y configuración de archivos de proyecto.

**Ver documentación:** [.template/setup/README.md](setup/README.md)

**Uso rápido:**
```bash
python .template/setup/setup.py --name mi-proyecto
```

## Implementación de Flujos

Scripts para orquestar la implementación de flujos de datos usando comandos de Cursor.

**Ver documentación:** [.template/flows/README.md](flows/README.md)

**Uso rápido:**
```bash
.template/flows/scripts/orchestrate_flow.sh --requirements flow_requirements.md
```

## Notas

- Ambos conjuntos de scripts son independientes
- El setup de proyecto se ejecuta una vez al crear un nuevo proyecto
- La implementación de flujos se puede ejecutar múltiples veces para diferentes flujos
- Todos los scripts preservan el template original para futuros usos
