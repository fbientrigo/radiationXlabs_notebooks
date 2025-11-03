{
  const int Nbins=32;
  TFile *_file0 = TFile::Open("cpld_data_second_run.root");
  TTree *tr =  (TTree *)_file0->Get("tr");
  int Ne =tr->GetEntries();
  TH2D *h;
  TMultiGraph* mg = new TMultiGraph();
  TGraph *gr[Nbins];
  
  for (int k =0;k<Nbins;k++){
    gr[k] = new TGraph(Ne);
    gr[k]->SetName(TString("gr")+k);
    gr[k]->SetLineStyle(kDashed);
    gr[k]->SetMarkerStyle(kFullDotMedium);
    mg->Add(gr[k]);
  }
  
  TCanvas *c = new TCanvas("c","c",960,720);
  
  Double_t tstmp;
  Int_t bit[Nbins];
  tr->SetBranchAddress("bit",bit);
  tr->SetBranchAddress("t", &tstmp);
  
  //// getting curves
  for (int i =0;i<Ne;i++){
    tr->GetEntry(i);
    for (int k =0;k<Nbins;k++){
      gr[k]->SetPoint(i,tstmp,bit[k]);
    }
  }

  mg->Draw("apl pmc plc");

  
  //////
  // ////ploting curves
  TLegendEntry *le;
  TLegend * leg = new TLegend(0.15,0.2,0.22,0.95);
  leg->SetTextSizePixels(16);
  Color_t color;
  gStyle->SetPalette(kRainBow);

  for (int k = 0;k<Nbins;k++){
    color = gr[k]->GetLineColor();
    leg->AddEntry(gr[k],TString("bit")+k,"lp");
  }
  leg->Draw();
  
  for (int k = 0;k<Nbins;k++){
    le = (TLegendEntry*)leg->GetListOfPrimitives()->At(k);
    color = ((TGraph *)le->GetObject())->GetLineColor();
    le->SetTextColor(color);
    le->SetTextColor(color);
  }
  leg->SetTextSizePixels(16);
  mg->GetXaxis()->SetTimeOffset(2,"gmt");
  mg->GetXaxis()->SetTimeDisplay(1);
  mg->GetXaxis()->SetTitle("t");
  mg->GetYaxis()->SetTitle("#Sigmaerrors ");
  mg->GetYaxis()->SetTitleOffset(-0.3);
  leg->SetBorderSize(1);
  c->Modified();
  /*
    c->SaveAs("cpld_bitfails.png");
   */
  // //////////
  // //// setting colors of the legend
  // // ((TLegendEntry *)leg->GetListOfPrimitives()->At(0))->SetTextColor();
  // // for (int k =0;k<32;k++){
  // //   le = (TLegendEntry *)leg->GetListOfPrimitives()->At(0);
  // //   color = ((TH2D*)le->GetObject())->GetLineColor();
  // //   le->SetTextColor(color);
  // // }
  // //leg->Draw();
  // c->Modified();
}
