import java.util.*;

public class Main {

    public static void main(String[] args) {
        Scanner entrada = new Scanner(System.in);
        mostrarBannerInicial();

        // Demanar el VOC a detectar
        String vocSeleccionat = demanarVOC(entrada);
        if (vocSeleccionat == null) return;

        // Triar el mode de puntuació
        ScoringConfig configuracio = demanarMode(entrada);
        System.out.println("\nConfiguracio: " + configuracio);

        // Llegir les dades del CSV
        System.out.println("\nLlegint Compound_OBP_binding.csv ...");
        List<OBPEntry> llistaOBPs;
        try {
            llistaOBPs = IobpdbReader.llegirPerVOC(vocSeleccionat);
        } catch (Exception error) {
            System.out.println("Error llegint el CSV: " + error.getMessage());
            return;
        }

        if (llistaOBPs.isEmpty()) {
            System.out.println("\nNo s'han trobat OBPs per a: " + vocSeleccionat);
            try {
                List<String> vocsDisponibles = IobpdbReader.cercarVOCs(vocSeleccionat);
                vocsDisponibles.forEach(v -> System.out.println("  - " + v));
            } catch (Exception ignorat) {}
            return;
        }

        System.out.println("  " + llistaOBPs.size() + " OBPs trobats amb afinitat per a aquest VOC.");

        // Calcular la puntuació i ordenar
        System.out.println("\nAplicant filtres i calculant Scores...");
        ScoreCalculator calculador = new ScoreCalculator(configuracio);
        List<OBPEntry> llistaOrdenada = calculador.ordenarOBPs(llistaOBPs);

        if (llistaOrdenada.isEmpty()) {
            System.out.println("\nCap OBP ha superat els filtres. Prova amb criteris menys restrictius.");
            return;
        }

        // Mostrar resultats
        mostrarResultats(llistaOrdenada, vocSeleccionat);
        entrada.close();
    }

    private static void mostrarBannerInicial() {
        System.out.println("  SCENTINEL-CODE  --  VOC Biosensor Designer");
        System.out.println();
    }

    private static String demanarVOC(Scanner entrada) {
        System.out.print("Introdueix el VOC que vols detectar: ");
        String textIntroduit = entrada.nextLine().trim();
        if (textIntroduit.isEmpty()) { System.out.println("Has d'introduir un VOC."); return null; }
        return textIntroduit;
    }

    private static ScoringConfig demanarMode(Scanner entrada) {
        System.out.println("\nTria el mode de puntuacio:");
        System.out.println("  [1] Automatic  ");
        System.out.println("  [2] Personalitzat");
        System.out.print("Opcio (1 o 2): ");
        String opcioEscollida = entrada.nextLine().trim();

        if (opcioEscollida.equals("2")) {
            System.out.println("\n--- Configuracio personalitzada ---");
            double pesAfinitat      = demanarNumero(entrada, "Pes afinitat    : ", 0, 1);
            double pesEspecificitat = demanarNumero(entrada, "Pes especificitat : ", 0, 1);
            double pesEstudis       = demanarNumero(entrada, "Pes estudis     : ", 0, 1);
            double kiMaxima         = demanarNumero(entrada, "Ki maxima (µM, ex: 30): ", 0.1, 10000);
            int    maxVOCsAlternatius = (int) demanarNumero(entrada, "Max VOCs alternatius : ", 0, 1000);
            try {
                return ScoringConfig.personalitzat(pesAfinitat, pesEspecificitat, pesEstudis, kiMaxima, maxVOCsAlternatius);
            } catch (IllegalArgumentException error) {
                System.out.println("  Avis: " + error.getMessage() + " -> usant mode automatic.");
            }
        }
        System.out.println("  -> Mode Automatic seleccionat.");
        return ScoringConfig.automatic();
    }

    private static void mostrarResultats(List<OBPEntry> llistaOrdenada, String nomVOC) {
        System.out.println();
        System.out.printf("  RESULTATS -- Millors OBPs per detectar: %s%n", nomVOC);
        System.out.printf("  %-4s %-22s %-10s %-7s %-10s %-8s%n",
                "#", "OBP", "Ki (µM)", "Aprox?", "VOCs alt.", "Score");

        for (int posicio = 0; posicio < llistaOrdenada.size(); posicio++) {
            OBPEntry obp = llistaOrdenada.get(posicio);
            String medalla = (posicio == 0) ? "**" : (posicio == 1) ? " 2" : (posicio == 2) ? " 3" : "  ";
            System.out.printf("  %s%-2d %-22s %-10.2f %-7s %-10d %-8.1f%n",
                    medalla, (posicio + 1),
                    obp.getNom(),
                    obp.getKiDelVOC(),
                    obp.isKiAproximada() ? "Si" : "No",
                    obp.getNombreVOCsAlternatius(),
                    obp.getPuntuacio());
        }

        System.out.println("================================================================");

        // Detalls del millor candidat
        OBPEntry millorOBP = llistaOrdenada.get(0);
        System.out.println("\n--- Detalls del millor candidat: " + millorOBP.getNom() + " ---");
        System.out.printf("  Ki amb el VOC target: %.2f µM%s%n",
                millorOBP.getKiDelVOC(), millorOBP.isKiAproximada() ? " (valor aproximat, era >X)" : "");
        System.out.println("  Estudis disponibles: " + millorOBP.getNombreEstudis());
        if (millorOBP.getVOCsAlternatius().isEmpty()) {
            System.out.println("  Afinitats alternatives: Cap (molt especific!)");
        } else {
            System.out.println("  Afinitats alternatives (" + millorOBP.getNombreVOCsAlternatius() + "):");
            millorOBP.getVOCsAlternatius().stream().limit(5)
                .forEach(v -> System.out.println("    - " + v));
            if (millorOBP.getNombreVOCsAlternatius() > 5)
                System.out.println("    ... i " + (millorOBP.getNombreVOCsAlternatius() - 5) + " mes.");
        }
        System.out.printf("  Score final: %.1f / 100%n", millorOBP.getPuntuacio());
    }

    private static double demanarNumero(Scanner entrada, String missatge, double minim, double maxim) {
        while (true) {
            try {
                System.out.print(missatge);
                double valor = Double.parseDouble(entrada.nextLine().trim());
                if (valor >= minim && valor <= maxim) return valor;
                System.out.println("  Valor fora de rang [" + minim + ", " + maxim + "]");
            } catch (NumberFormatException e) {
                System.out.println("  Introdueix un numero valid.");
            }
        }
    }
}
