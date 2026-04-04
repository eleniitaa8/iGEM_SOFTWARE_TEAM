import java.util.ArrayList;
import java.util.List;

// Representa un OBP candidat per al biosensor.
// Conté la Ki amb el VOC target i totes les afinitats alternatives.

public class OBPEntry {

    private String nom;
    private double kiDelVOC;
    private boolean kiEsAproximada;
    private List<String> vocsAlternatius;
    private int nombreEstudis;
    private double puntuacio;

    public OBPEntry(String nom, double kiDelVOC, boolean kiEsAproximada) {
        this.nom             = nom;
        this.kiDelVOC        = kiDelVOC;
        this.kiEsAproximada  = kiEsAproximada;
        this.vocsAlternatius = new ArrayList<>();
        this.nombreEstudis   = 0;
        this.puntuacio       = 0.0;
    }

    public String       getNom()                    { return nom; }
    public double       getKiDelVOC()               { return kiDelVOC; }
    public boolean      isKiAproximada()             { return kiEsAproximada; }
    public int          getNombreEstudis()           { return nombreEstudis; }
    public List<String> getVOCsAlternatius()         { return vocsAlternatius; }
    public int          getNombreVOCsAlternatius()   { return vocsAlternatius.size(); }
    public double       getPuntuacio()               { return puntuacio; }

    public void setPuntuacio(double puntuacio)           { this.puntuacio = puntuacio; }
    public void setNombreEstudis(int nombre)             { this.nombreEstudis = nombre; }
    public void afegirVOCAlternatiu(String nomVOC)       { this.vocsAlternatius.add(nomVOC); }
}
