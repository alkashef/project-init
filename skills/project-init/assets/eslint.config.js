// ESLint configuration. It enforces the JavaScript rules in CLAUDE.md.
// Never disable a rule to make a change pass. Fix the code.
import js from "@eslint/js";
import globals from "globals";

export default [
  { ignores: ["site/**", "node_modules/**"] },
  js.configs.recommended,
  {
    files: ["src/**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: { ...globals.browser },
    },
    rules: {
      // Code-smell limits (see Code smells).
      "max-lines-per-function": ["error", { max: 20, skipBlankLines: true, skipComments: true }],
      "max-params": ["error", 4],
      complexity: ["error", 8],
      "max-lines": ["warn", { max: 300, skipBlankLines: true, skipComments: true }],
      // Plain, predictable code.
      "no-var": "error",
      "prefer-const": "error",
      eqeqeq: "error",
      // Only log.js uses console, and only api.js calls fetch.
      "no-console": "error",
      "no-restricted-globals": ["error", { name: "fetch", message: "Only api.js calls fetch." }],
      "no-restricted-syntax": [
        "error",
        {
          selector: "Program > VariableDeclaration[kind='let']",
          message: "No mutable module-level state. Create state in main.js and pass it in.",
        },
        {
          selector: "ExportNamedDeclaration > VariableDeclaration[kind='let']",
          message: "No mutable module-level state. Create state in main.js and pass it in.",
        },
        {
          selector: "AssignmentExpression[left.property.name='innerHTML']",
          message: "Use textContent or a <template>. Never build HTML from data.",
        },
      ],
    },
  },
  { files: ["src/api.js"], rules: { "no-restricted-globals": "off" } },
  { files: ["src/log.js"], rules: { "no-console": "off" } },
  { files: ["tests/**/*.js"], languageOptions: { globals: { ...globals.node } } },
];
