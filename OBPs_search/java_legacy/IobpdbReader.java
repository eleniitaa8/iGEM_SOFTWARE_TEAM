import java.io.*;
import java.util.*;

public class IobpdbReader {

    private static final String RUTA_CSV = "Compound_OBP_binding.csv";

    // Converteix el valor de Ki en brut a un número, i indica si és aproximat
    public static double[] convertirKi(String valorBrut) {

        if (valorBrut == null) return null;
        valorBrut = valorBrut.trim();
        if (valorBrut.isEmpty() || valorBrut.equals("-")) return null;

        boolean esAproximar = false;
        if (valorBrut.startsWith(">")) {
            esAproximar = true;
            valorBrut = valorBrut.replace(">", "").trim();
        }
        // Eliminar caràcters estranys
        valorBrut = valorBrut.replaceAll("[^0-9.]", "");
        if (valorBrut.isEmpty()) return null;

        try {
            double numero = Double.parseDouble(valorBrut);
            return new double[]{numero, esAproximar ? 1.0 : 0.0};
        } catch (NumberFormatException e) {
            return null;
        }
    }


    public static List<OBPEntry> llegirPerVOC(String nomVOC) throws IOException {

        BufferedReader lector = new BufferedReader(
            new InputStreamReader(new FileInputStream(RUTA_CSV), "UTF-8"));

        // Llegir capçalera
        String lineaCapcalera = lector.readLine();
        if (lineaCapcalera == null) { lector.close(); return new ArrayList<>(); }
        // Eliminar BOM si existeix
        if (lineaCapcalera.startsWith("\uFEFF")) lineaCapcalera = lineaCapcalera.substring(1);

        String[] nomsColumnes = llegirLineaCSV(lineaCapcalera);
        int nombreOBPs = nomsColumnes.length - 2;

        List<String[]> totesLesFiles = new ArrayList<>();
        String linia;
        while ((linia = lector.readLine()) != null) {
            if (!linia.trim().isEmpty()) totesLesFiles.add(llegirLineaCSV(linia));
        }
        lector.close();

        // Trobar la fila del VOC que estem buscant
        int filaVOCTrobat = -1;
        for (int i = 0; i < totesLesFiles.size(); i++) {
            String[] fila = totesLesFiles.get(i);
            if (fila.length < 2) continue;
            if (fila[1].toLowerCase().contains(nomVOC.toLowerCase())) {
                filaVOCTrobat = i;
                break;
            }
        }

        if (filaVOCTrobat == -1) return new ArrayList<>();

        String[] filaDelVOC = totesLesFiles.get(filaVOCTrobat);
        System.out.println("  VOC trobat: " + filaDelVOC[1]);

        // Per cada OBP: comptar quants VOCs reconeix (promiscuïtat)
        int[] nombreEstudisPerOBP = new int[nombreOBPs];
        for (String[] fila : totesLesFiles) {
            for (int columna = 2; columna < Math.min(fila.length, nomsColumnes.length); columna++) {
                double[] ki = convertirKi(fila[columna]);
                if (ki != null) nombreEstudisPerOBP[columna - 2]++;
            }
        }

        // Construir la llista d'OBPs candidats per al VOC buscat
        List<OBPEntry> llistaOBPsCandidats = new ArrayList<>();

        for (int columna = 2; columna < Math.min(filaDelVOC.length, nomsColumnes.length); columna++) {
            double[] kiCalculada = convertirKi(filaDelVOC[columna]);
            if (kiCalculada == null) continue;

            String nomOBP     = nomsColumnes[columna];
            double valorKi    = kiCalculada[0];
            boolean esAprox   = kiCalculada[1] == 1.0;

            OBPEntry obp = new OBPEntry(nomOBP, valorKi, esAprox);
            obp.setNombreEstudis(nombreEstudisPerOBP[columna - 2]);

            // Afegir VOCs alternatius que reconeix aquest OBP
            int columnaOBP = columna;
            for (int numFila = 0; numFila < totesLesFiles.size(); numFila++) {
                if (numFila == filaVOCTrobat) continue;
                String[] filaAlternativa = totesLesFiles.get(numFila);
                if (filaAlternativa.length <= columnaOBP) continue;
                double[] kiAlternativa = convertirKi(filaAlternativa[columnaOBP]);
                if (kiAlternativa != null && filaAlternativa.length > 1) {
                    String nomVOCAlternatiu = filaAlternativa[1].length() > 30
                        ? filaAlternativa[1].substring(0, 30) + "..."
                        : filaAlternativa[1];
                    obp.afegirVOCAlternatiu(nomVOCAlternatiu + " (Ki=" + String.format("%.1f", kiAlternativa[0]) + ")");
                }
            }

            llistaOBPsCandidats.add(obp);
        }

        return llistaOBPsCandidats;
    }


    // Llista tots els noms de VOCs disponibles al CSV que contenen el text cercat
    public static List<String> cercarVOCs(String textCerca) throws IOException {
        BufferedReader lector = new BufferedReader(
            new InputStreamReader(new FileInputStream(RUTA_CSV), "UTF-8"));
        lector.readLine(); // saltar capçalera
        List<String> resultats = new ArrayList<>();
        String linia;
        while ((linia = lector.readLine()) != null) {
            String[] fila = llegirLineaCSV(linia);
            if (fila.length > 1 && fila[1].toLowerCase().contains(textCerca.toLowerCase())) {
                resultats.add(fila[1]);
            }
        }
        lector.close();
        return resultats;
    }

    // Parseja una línia CSV tenint en compte camps entre cometes
    private static String[] llegirLineaCSV(String linia) {
        List<String> camps = new ArrayList<>();
        boolean dentreDeCometes = false;
        StringBuilder campActual = new StringBuilder();
        for (int i = 0; i < linia.length(); i++) {
            char caracter = linia.charAt(i);
            if (caracter == '"') {
                dentreDeCometes = !dentreDeCometes;
            } else if (caracter == ',' && !dentreDeCometes) {
                camps.add(campActual.toString().trim());
                campActual = new StringBuilder();
            } else {
                campActual.append(caracter);
            }
        }
        camps.add(campActual.toString().trim());
        return camps.toArray(new String[0]);
    }
}
