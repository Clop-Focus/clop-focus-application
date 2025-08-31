import React from 'react';
import BothModsIntegration from '../components/BothModsIntegration';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { ArrowLeft, Info } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const BothModsPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/')}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Voltar
            </Button>
            <h1 className="text-3xl font-bold">BothMods Integration</h1>
          </div>
        </div>

        {/* Info Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="h-5 w-5" />
              Sobre a Integração
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              Esta integração combina os modelos MediaPipe Face e Pose usando qai_hub_models 
              para detecção em tempo real de landmarks faciais e corporais.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <h4 className="font-semibold">MediaPipe Face</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Detecção de faces</li>
                  <li>• Landmarks faciais</li>
                  <li>• Bounding boxes</li>
                </ul>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-semibold">MediaPipe Pose</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Detecção de pose</li>
                  <li>• Landmarks corporais</li>
                  <li>• Esqueleto 3D</li>
                </ul>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-semibold">qai_hub_models</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Modelos otimizados</li>
                  <li>• Processamento rápido</li>
                  <li>• Integração Qualcomm</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* BothMods Integration Component */}
        <BothModsIntegration />
      </div>
    </div>
  );
};

export default BothModsPage;


