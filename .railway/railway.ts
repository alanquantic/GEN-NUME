import { defineRailway, github, project, service, volume } from "railway/iac";
// This repository manages only its own resources in the environment. Other
// repositories export their own partial name.
// See https://docs.railway.com/infrastructure-as-code#multi-repo-projects
export const partial = "GEN-NUME";
export default defineRailway(() => {
  // Volumen persistente con los PDFs y jobs generados. `railway config migrate`
  // no lo incluye: sin esta declaración el plan lo desmonta del servicio.
  const data = volume("gen-nume-volume", { region: "us-west2", sizeMB: 50000 });

  const GENNUME = service("GEN-NUME", {
    source: github("alanquantic/GEN-NUME", { branch: "main", checkSuites: false }),
    build: { buildEnvironment: "V3", builder: "DOCKERFILE", dockerfilePath: "Dockerfile" },
    healthcheck: "/health",
    healthcheckTimeout: 100,
    replicas: { "us-west2": 1 },
    deploy: { restartPolicyMaxRetries: 3 },
    networking: { privateNetworkEndpoint: "gen-nume" },
    volumeMounts: { "/data": data },
  });

  return project("GEN NUME", {
    variables: { managed: false },
    resources: [GENNUME, data],
  });
});
