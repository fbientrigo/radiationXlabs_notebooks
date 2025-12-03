void TTF_2()
{
//=========Macro generated from canvas: c1/c1
//=========  (Tue Feb 14 02:20:51 2023) by ROOT version 6.18/02
   TCanvas *c1 = new TCanvas("c1", "c1",10,64,1024,704);
   c1->Range(-55.75758,-4.4625,501.8182,40.1625);
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
   
   TH1D *hr2TTF__1 = new TH1D("hr2TTF__1","Time to failure run 2",100,0,1000);
   hr2TTF__1->SetBinContent(2,11);
   hr2TTF__1->SetBinContent(3,15);
   hr2TTF__1->SetBinContent(4,13);
   hr2TTF__1->SetBinContent(5,15);
   hr2TTF__1->SetBinContent(6,21);
   hr2TTF__1->SetBinContent(8,5);
   hr2TTF__1->SetBinContent(9,34);
   hr2TTF__1->SetBinContent(11,1);
   hr2TTF__1->SetBinContent(12,6);
   hr2TTF__1->SetBinContent(15,5);
   hr2TTF__1->SetBinContent(18,25);
   hr2TTF__1->SetBinContent(24,19);
   hr2TTF__1->SetBinContent(36,32);
   hr2TTF__1->SetBinContent(71,53);
   hr2TTF__1->SetBinContent(101,570);
   hr2TTF__1->SetEntries(825);
   
   TPaveStats *ptstats = new TPaveStats(0.78,0.835,0.98,0.995,"brNDC");
   ptstats->SetName("stats");
   ptstats->SetBorderSize(2);
   ptstats->SetFillColor(0);
   ptstats->SetTextAlign(12);
   ptstats->SetTextFont(22);
   TText *ptstats_LaTex = ptstats->AddText("hr2TTF");
   ptstats_LaTex->SetTextSize(0.0368);
   ptstats_LaTex = ptstats->AddText("Entries = 825    ");
   ptstats_LaTex = ptstats->AddText("Mean  =  137.7");
   ptstats_LaTex = ptstats->AddText("Std Dev   =  113.7");
   ptstats->SetOptStat(1111);
   ptstats->SetOptFit(0);
   ptstats->Draw();
   hr2TTF__1->GetListOfFunctions()->Add(ptstats);
   ptstats->SetParent(hr2TTF__1);
   hr2TTF__1->SetFillColor(1);
   hr2TTF__1->SetLineWidth(2);
   hr2TTF__1->GetXaxis()->SetTitle("t s");
   hr2TTF__1->GetXaxis()->SetRange(1,46);
   hr2TTF__1->GetXaxis()->SetLabelFont(22);
   hr2TTF__1->GetXaxis()->SetLabelSize(0.05);
   hr2TTF__1->GetXaxis()->SetTitleSize(0.05);
   hr2TTF__1->GetXaxis()->SetTitleOffset(0.75);
   hr2TTF__1->GetXaxis()->SetTitleFont(22);
   hr2TTF__1->GetYaxis()->SetTitle("# failures");
   hr2TTF__1->GetYaxis()->SetLabelFont(22);
   hr2TTF__1->GetYaxis()->SetLabelSize(0.05);
   hr2TTF__1->GetYaxis()->SetTitleSize(0.05);
   hr2TTF__1->GetYaxis()->SetTitleOffset(0.75);
   hr2TTF__1->GetYaxis()->SetTitleFont(22);
   hr2TTF__1->GetZaxis()->SetLabelFont(22);
   hr2TTF__1->GetZaxis()->SetLabelOffset(-0.04);
   hr2TTF__1->GetZaxis()->SetLabelSize(0.02);
   hr2TTF__1->GetZaxis()->SetTitleSize(0.05);
   hr2TTF__1->GetZaxis()->SetTickLength(0.002);
   hr2TTF__1->GetZaxis()->SetTitleOffset(0.75);
   hr2TTF__1->GetZaxis()->SetTitleFont(22);
   hr2TTF__1->Draw("hist");
   
   TPaveText *pt = new TPaveText(0.01,0.945,0.3568102,0.995,"blNDC");
   pt->SetName("title");
   pt->SetBorderSize(0);
   pt->SetFillColor(0);
   pt->SetTextFont(22);
   TText *pt_LaTex = pt->AddText("Time to failure run 2");
   pt->Draw();
   c1->Modified();
   c1->cd();
   c1->SetSelected(c1);
}
