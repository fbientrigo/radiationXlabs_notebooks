void cpld_TTF_3()
{
//=========Macro generated from canvas: c1/c1
//=========  (Tue Feb 14 02:30:25 2023) by ROOT version 6.18/02
   TCanvas *c1 = new TCanvas("c1", "c1",10,64,1024,704);
   c1->Range(-67.87879,-4.4625,610.9091,40.1625);
   c1->SetFillColor(0);
   c1->SetBorderMode(0);
   c1->SetBorderSize(2);
   c1->SetGridx();
   c1->SetGridy();
   c1->SetTickx(1);
   c1->SetTicky(1);
   c1->SetRightMargin(0.075);
   c1->SetFrameBorderMode(0);
   c1->SetFrameBorderMode(0);
   
   TH1D *hr3TTF__1 = new TH1D("hr3TTF__1","Time to failure run 3",100,0,1000);
   hr3TTF__1->SetBinContent(1,1);
   hr3TTF__1->SetBinContent(2,34);
   hr3TTF__1->SetBinContent(3,23);
   hr3TTF__1->SetBinContent(4,14);
   hr3TTF__1->SetBinContent(5,7);
   hr3TTF__1->SetBinContent(6,4);
   hr3TTF__1->SetBinContent(7,1);
   hr3TTF__1->SetBinContent(8,6);
   hr3TTF__1->SetBinContent(9,5);
   hr3TTF__1->SetBinContent(11,1);
   hr3TTF__1->SetBinContent(12,2);
   hr3TTF__1->SetBinContent(15,2);
   hr3TTF__1->SetBinContent(18,3);
   hr3TTF__1->SetBinContent(24,6);
   hr3TTF__1->SetBinContent(36,9);
   hr3TTF__1->SetBinContent(71,54);
   hr3TTF__1->SetBinContent(101,475);
   hr3TTF__1->SetEntries(647);
   
   TPaveStats *ptstats = new TPaveStats(0.78,0.835,0.98,0.995,"brNDC");
   ptstats->SetName("stats");
   ptstats->SetBorderSize(2);
   ptstats->SetFillColor(0);
   ptstats->SetTextAlign(12);
   ptstats->SetTextFont(22);
   TText *ptstats_LaTex = ptstats->AddText("hr3TTF");
   ptstats_LaTex->SetTextSize(0.0368);
   ptstats_LaTex = ptstats->AddText("Entries = 647    ");
   ptstats_LaTex = ptstats->AddText("Mean  =  74.66");
   ptstats_LaTex = ptstats->AddText("Std Dev   =  97.37");
   ptstats->SetOptStat(1111);
   ptstats->SetOptFit(0);
   ptstats->Draw();
   hr3TTF__1->GetListOfFunctions()->Add(ptstats);
   ptstats->SetParent(hr3TTF__1);
   hr3TTF__1->SetFillColor(1);
   hr3TTF__1->SetLineWidth(2);
   hr3TTF__1->GetXaxis()->SetTitle("t s");
   hr3TTF__1->GetXaxis()->SetRange(1,56);
   hr3TTF__1->GetXaxis()->SetLabelFont(22);
   hr3TTF__1->GetXaxis()->SetLabelSize(0.05);
   hr3TTF__1->GetXaxis()->SetTitleSize(0.05);
   hr3TTF__1->GetXaxis()->SetTitleOffset(0.75);
   hr3TTF__1->GetXaxis()->SetTitleFont(22);
   hr3TTF__1->GetYaxis()->SetTitle("# failures");
   hr3TTF__1->GetYaxis()->SetLabelFont(22);
   hr3TTF__1->GetYaxis()->SetLabelSize(0.05);
   hr3TTF__1->GetYaxis()->SetTitleSize(0.05);
   hr3TTF__1->GetYaxis()->SetTitleOffset(0.75);
   hr3TTF__1->GetYaxis()->SetTitleFont(22);
   hr3TTF__1->GetZaxis()->SetLabelFont(22);
   hr3TTF__1->GetZaxis()->SetLabelOffset(-0.04);
   hr3TTF__1->GetZaxis()->SetLabelSize(0.02);
   hr3TTF__1->GetZaxis()->SetTitleSize(0.05);
   hr3TTF__1->GetZaxis()->SetTickLength(0.002);
   hr3TTF__1->GetZaxis()->SetTitleOffset(0.75);
   hr3TTF__1->GetZaxis()->SetTitleFont(22);
   hr3TTF__1->Draw("hist");
   
   TPaveText *pt = new TPaveText(0.01,0.945,0.3568102,0.995,"blNDC");
   pt->SetName("title");
   pt->SetBorderSize(0);
   pt->SetFillColor(0);
   pt->SetTextFont(22);
   TText *pt_LaTex = pt->AddText("Time to failure run 3");
   pt->Draw();
   c1->Modified();
   c1->cd();
   c1->SetSelected(c1);
}
