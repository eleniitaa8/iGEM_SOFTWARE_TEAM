import java.util.*;

public class ScoreCalculator {

    private ScoringConfig configuracio;

    public ScoreCalculator(ScoringConfig configuracio) {
        this.configuracio = configuracio;
    }

    public List<OBPEntry> ordenarOBPs(List<OBPEntry> llistaOBPs) {

        // Trobar els valors màxims per poder normalitzar les puntuacions
        double kiMaximaTrobada    = 0;
        int    estudisMaximsTrobats = 0;
        int    vocsAlternatiusMaxims = 0;

        for (OBPEntry obp : llistaOBPs) {
            if (obp.getKiDelVOC()             > kiMaximaTrobada)      kiMaximaTrobada = obp.getKiDelVOC();
            if (obp.getNombreEstudis()         > estudisMaximsTrobats) estudisMaximsTrobats = obp.getNombreEstudis();
            if (obp.getNombreVOCsAlternatius() > vocsAlternatiusMaxims) vocsAlternatiusMaxims = obp.getNombreVOCsAlternatius();
        }

        double kiMaximaReferencia      = Math.max(kiMaximaTrobada,      configuracio.getKiMaxima());
        int    estudisMaximsReferencia  = Math.max(estudisMaximsTrobats, 1);
        int    vocsAltsMaximsReferencia = Math.max(vocsAlternatiusMaxims, 1);

        // Calcular la puntuació de cada OBP
        for (OBPEntry obp : llistaOBPs) {
            double puntuacioAfinitat      = 100.0 * (1.0 - obp.getKiDelVOC() / kiMaximaReferencia);
            double puntuacioEspecificitat = 100.0 * (1.0 - (double) obp.getNombreVOCsAlternatius() / vocsAltsMaximsReferencia);
            double puntuacioEstudis       = 100.0 * ((double) obp.getNombreEstudis() / estudisMaximsReferencia);

            puntuacioAfinitat      = Math.max(0, Math.min(100, puntuacioAfinitat));
            puntuacioEspecificitat = Math.max(0, Math.min(100, puntuacioEspecificitat));
            puntuacioEstudis       = Math.max(0, Math.min(100, puntuacioEstudis));

            double puntuacioFinal = (puntuacioAfinitat      * configuracio.getPesAfinitat())
                                  + (puntuacioEspecificitat * configuracio.getPesEspecificitat())
                                  + (puntuacioEstudis       * configuracio.getPesEstudis());

            // Penalitzar si la Ki és aproximada (valor ">X")
            if (obp.isKiAproximada()) puntuacioFinal = Math.max(0, puntuacioFinal - 10);

            obp.setPuntuacio(puntuacioFinal);
        }

        // Ordenar de major a menor puntuació
        llistaOBPs.sort(Comparator.comparingDouble(OBPEntry::getPuntuacio).reversed());
        return llistaOBPs;
    }
}
