{
  auto c = new TCanvas("c","c",800,600);
  Double_t tr2min = 1.6631000e+09, tr2max = 1.6638000e+09;
  Double_t tr3min = 1.6679400e+09, tr3max = 1.6686400e+09;

  Int_t Nbin = 1000;
  Double_t ttfmin = 0,ttfmax=1000;
  Double_t ftfmin = 0,ftfmax=10e6; 

  TTree *tr2;
  
  TFile *fr2B = TFile::Open("beam_data_second_run.root");
  TH1D *hr2B = new TH1D("hr2B","Fluence run 2",Nbin,tr2min,tr2max);
  TFile *fr3B = TFile::Open("beam_data_third_run.root");
  TH1D *hr3B = new TH1D("hr3B","Fluence run 3",Nbin,tr3min,tr3max);

  TFile *fr2 = TFile::Open("cpld_data_second_run.root");
  TH1D *hr2 = new TH1D("hr2","Errors run 2",Nbin,tr2min,tr2max);
  TH1D *hr2TTF = new TH1D("hr2TTF","Time to failure run 2",Nbin/10,ttfmin,ttfmax);
  TH1D *hr2FTF = new TH1D("hr2FTF","Fluence to failure run 2",Nbin/10,ftfmin,ftfmax);
  TFile *fr3 = TFile::Open("cpld_data_third_run.root");
  TH1D *hr3 = new TH1D("hr3","Errors run 3",Nbin,tr3min,tr3max);
  TH1D *hr3TTF = new TH1D("hr3TTF","Time to failure run 3",Nbin/10,ttfmin,ttfmax);
  TH1D *hr3FTF = new TH1D("hr3FTF","Fluence to failure run 3",Nbin/10,ftfmin,ftfmax);

  
  Double_t TID, HEH, N1MeV,t,tl=0,th=0,vl,vh,vl2,vh2;

  Int_t bitr2[32], bitPr2[32], bitr3[16], bitPr3[16];
  int nbin = 1, nbitsr2 = 32, nbitsr3 = 16;  
  ////////// Run 2 analysis
  ////// Fluence
  fr2B->cd();
  tr2 = (TTree *)fr2B->Get("tr");
  tr2->SetBranchAddress("t",&t);
  tr2->SetBranchAddress("HEH",&HEH);
  tr2->SetBranchAddress("TID",&TID);
  tr2->SetBranchAddress("N1MeV",&N1MeV);


  tl = tr2min;
  th = hr2B->GetBinLowEdge(nbin+1);
  tr2->GetEntry(0);
  vl = HEH;
  for (int k = 0; k < tr2->GetEntries(); k++){
    tr2->GetEntry(k);
    if (t > th){
      vh = HEH;
      hr2B->Fill((tl+th)/2,vh-vl);
      hr2B->SetBinError(nbin,sqrt(vh)+sqrt(vl));
      vl = vh;
      tl = th;
      nbin++;
      if ((nbin + 1) <= hr2B->GetNbinsX()) th = hr2B->GetBinLowEdge(nbin+1);
    }
  }
  hr2B->Draw("histe");
  ///// CPLD ERRORS
  fr2->cd();
  tr2 = (TTree *)fr2->Get("tr");
  tr2->SetBranchAddress("t",&t);
  // tr2->SetBranchAddress(TString("bit[")+nbitsr2+"]/I",&bitr2);
  // tr2->SetBranchAddress(TString("bitP[")+nbitsr2+"]/I",&bitPr2);
  tr2->SetBranchAddress(TString("bit"),bitr2);
  tr2->SetBranchAddress(TString("bitP"),bitPr2);

  nbin = 1;
  tl = tr2min;
  th = hr2->GetBinLowEdge(nbin+1);
  tr2->GetEntry(0);
  vl = 0;
  for (int n = 0;n<nbitsr2;n++){vl += bitr2[n];}
  for (int n = 0;n<nbitsr2;n++){vl += bitPr2[n];}
  for (int k = 0; k < tr2->GetEntries(); k++){
    tr2->GetEntry(k);
    if (t > th){
      vh = 0;
      vh2 = 0;
      for (int n = 0;n<nbitsr2;n++){vh += bitr2[n];}
      for (int n = 0;n<nbitsr2;n++){vh2 += bitPr2[n];}
      hr2->Fill((tl+th)/2,vh-vl);
      hr2->SetBinError(nbin,sqrt(vh)+sqrt(vl));
      if ((th-tl)/(vh-vl) > 10 )hr2TTF->Fill((th-tl)/(vh-vl -vh2 + vl2));
      vl = vh;
      vl2 = vh2;
      tl = th;
      nbin++;
      if ((nbin + 1) <= hr2->GetNbinsX()) th = hr2->GetBinLowEdge(nbin+1);
    }
  }
  hr2->Draw("hist");
  ////////////////
  //hr2TTF->Draw("hist");
  hr2B->Divide(hr2);
  for (int k = 0; k<hr2B->GetNbinsX();k++){
    vl = hr2B->GetBinContent(k+1);
    if (vl>0)hr2FTF->Fill(vl);
  }
  hr2FTF->Draw("hist");

  //hr2->Draw("hist");
  hr2TTF->Draw("hist");

  ////////// Run 3 analysis
  ////// Fluence
  fr3B->cd();
  tr3 = (TTree *)fr3B->Get("tr");
  tr3->SetBranchAddress("t",&t);
  tr3->SetBranchAddress("HEH",&HEH);
  tr3->SetBranchAddress("TID",&TID);
  tr3->SetBranchAddress("N1MeV",&N1MeV);


  tl = tr3min;
  th = hr3B->GetBinLowEdge(nbin+1);
  tr3->GetEntry(0);
  vl = HEH;
  for (int k = 0; k < tr3->GetEntries(); k++){
    tr3->GetEntry(k);
    if (t > th){
      vh = HEH;
      hr3B->Fill((tl+th)/2,vh-vl);
      hr3B->SetBinError(nbin,sqrt(vh)+sqrt(vl));
      vl = vh;
      tl = th;
      nbin++;
      if ((nbin + 1) <= hr3B->GetNbinsX()) th = hr3B->GetBinLowEdge(nbin+1);
    }
  }
  hr3B->Draw("histe");
  ///// CPLD ERRORS
  fr3->cd();
  tr3 = (TTree *)fr3->Get("tr");
  tr3->SetBranchAddress("t",&t);
  // tr3->SetBranchAddress(TString("bit[")+nbitsr3+"]/I",&bitr3);
  // tr3->SetBranchAddress(TString("bitP[")+nbitsr3+"]/I",&bitPr3);
  tr3->SetBranchAddress(TString("bit"),bitr3);
  tr3->SetBranchAddress(TString("bitP"),bitPr3);

  nbin = 1;
  tl = tr3min;
  th = hr3->GetBinLowEdge(nbin+1);
  tr3->GetEntry(0);
  vl = 0;
  for (int n = 0;n<nbitsr3;n++){vl += bitr3[n];}
  for (int n = 0;n<nbitsr3;n++){vl += bitPr3[n];}
  for (int k = 0; k < tr3->GetEntries(); k++){
    tr3->GetEntry(k);
    if (t > th){
      vh = 0;
      vh2 = 0;
      for (int n = 0;n<nbitsr3;n++){vh += bitr3[n];}
      for (int n = 0;n<nbitsr3;n++){vh2 += bitPr3[n];}
      hr3->Fill((tl+th)/2,vh-vl);
      hr3->SetBinError(nbin,sqrt(vh)+sqrt(vl));
      if ((th-tl)/(vh-vl) > 10 )hr3TTF->Fill((th-tl)/(vh-vl -vh2 + vl2));
      vl = vh;
      vl2 = vh2;
      tl = th;
      nbin++;
      if ((nbin + 1) <= hr3->GetNbinsX()) th = hr3->GetBinLowEdge(nbin+1);
    }
  }
  hr3->Draw("hist");
  ////////////////
  //hr3TTF->Draw("hist");
  hr3B->Divide(hr3);
  for (int k = 0; k<hr3B->GetNbinsX();k++){
    vl = hr3B->GetBinContent(k+1);
    if (vl>0)hr3FTF->Fill(vl);
  }
  hr3FTF->Draw("hist");

  //hr3->Draw("hist");
  hr3TTF->Draw("hist");

  
  
}
